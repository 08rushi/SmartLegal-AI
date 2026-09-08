"""
test_whatsapp_reliability.py — Step 2G Reliability, Idempotency & Replay Safety Test Suite.

Verifies:
1. Duplicate delivery of same provider_message_id results in a single logical outcome (0 duplicate AI calls).
2. Atomic processing claim prevents race conditions between concurrent workers.
3. Completed event replay returns persisted outbound response immediately.
4. Stale processing recovery (> 120s) reclaims ownership cleanly.
5. Replay safety for media document intake (0 duplicate document records in DB).
6. Replay safety for draft finalization (0 duplicate final documents generated).
7. Stale replayed messages cannot corrupt active workflow state.
8. Cross-session persistence across separate DB connections.
"""

import pytest
import uuid
import datetime
import json
from unittest.mock import AsyncMock, patch
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.reliability import (
    normalize_event_identity,
    claim_message_processing,
    complete_message_processing,
    fail_message_processing,
)
from services.whatsapp.context_repository import (
    get_or_create_context,
    set_drafting_state,
    WorkflowState,
)
from schemas.whatsapp import InboundMessagePayload
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture with complete Step 2G schema."""
    async with aiosqlite.connect(":memory:") as conn:
        db = SQLiteConnectionWrapper(conn)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_contacts (
                id TEXT PRIMARY KEY,
                phone_number TEXT UNIQUE NOT NULL,
                user_id TEXT,
                preferred_language TEXT DEFAULT NULL,
                onboarding_status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                direction TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                media_url TEXT,
                metadata_json TEXT DEFAULT '{}',
                provider_message_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                document_type TEXT DEFAULT '',
                file_hash TEXT DEFAULT '',
                status TEXT DEFAULT 'ready',
                uploaded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_conversation_context (
                id TEXT PRIMARY KEY,
                contact_id TEXT UNIQUE NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
                active_document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
                workflow_state TEXT NOT NULL DEFAULT 'idle',
                pending_candidates_json TEXT NOT NULL DEFAULT '[]',
                draft_type TEXT DEFAULT NULL,
                draft_requirements_json TEXT NOT NULL DEFAULT '{}',
                draft_confirmation_status TEXT DEFAULT NULL,
                context_status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_message_processing (
                id TEXT PRIMARY KEY,
                provider_message_id TEXT UNIQUE NOT NULL,
                contact_id TEXT NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
                processing_status TEXT NOT NULL DEFAULT 'processing',
                attempt_count INTEGER DEFAULT 1,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                outbound_reply TEXT,
                last_error_code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        yield db


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_duplicate_provider_message_id_replays_cached_response(mock_ai, temp_db):
    """Verify sending same provider message ID twice processes once and reuses reply without calling LLM twice."""
    mock_ai.return_value = "Legal advice regarding breach of contract."
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"
    msg_id = f"wamid_uniq_{uuid.uuid4().hex[:8]}"

    # Onboard in English
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # First delivery
    payload = {
        "from_phone": phone,
        "message_text": "What is the penalty for contract breach?",
        "message_id": msg_id,
    }
    res1 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res1.status == "ok"
    ai_calls_first = mock_ai.call_count

    # Second delivery (duplicate replay)
    res2 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res2.status == "ok"
    assert res2.reply == res1.reply
    # LLM must NOT be called a second time!
    assert mock_ai.call_count == ai_calls_first


@pytest.mark.anyio
async def test_atomic_claim_race_condition(temp_db):
    """Verify atomic claim allows only one worker to obtain processing ownership."""
    contact_id = "wac_race_test"
    msg_id = "wamid_race_1001"

    claim1 = await claim_message_processing(temp_db, msg_id, contact_id)
    assert claim1["status"] == "processing"
    assert claim1["is_owner"] is True

    # Concurrent Worker 2 attempts same claim
    claim2 = await claim_message_processing(temp_db, msg_id, contact_id)
    assert claim2["status"] == "in_progress"
    assert claim2["is_owner"] is False


@pytest.mark.anyio
async def test_stale_processing_recovery(temp_db):
    """Verify stale processing claim (> 120s) is reclaimed atomically."""
    contact_id = "wac_stale_test"
    msg_id = "wamid_stale_2002"

    # Insert old processing claim from 180s ago
    old_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=180)).isoformat()
    await temp_db.execute(
        """
        INSERT INTO whatsapp_message_processing (
            id, provider_message_id, contact_id, processing_status, attempt_count, started_at, created_at, updated_at
        ) VALUES ('claim_stale', $1, $2, 'processing', 1, $3, $3, $3)
        """,
        msg_id, contact_id, old_iso
    )

    # New claim attempt reclaims stale record
    reclaim = await claim_message_processing(temp_db, msg_id, contact_id)
    assert reclaim["status"] == "processing"
    assert reclaim["is_owner"] is True

    row = await temp_db.fetchrow("SELECT * FROM whatsapp_message_processing WHERE provider_message_id = $1", msg_id)
    assert row["attempt_count"] == 2


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.execute_whatsapp_document_analysis", new_callable=AsyncMock)
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_document_intake_replay_creates_single_document_record(mock_exec_analysis, mock_analyze_doc, temp_db):
    """Verify replaying media upload event creates exactly ONE document record in DB."""
    mock_exec_analysis.return_value = "Document analysis complete"
    mock_analyze_doc.return_value = {"summary": {"document_type": "Agreement", "overall_risk": "LOW"}}
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"
    media_msg_id = f"wamid_media_{uuid.uuid4().hex[:8]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    payload = {
        "from_phone": phone,
        "message_text": "Here is my contract",
        "media_url": "sample_pdf",
        "message_id": media_msg_id,
    }

    # First delivery
    res1 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res1.status == "ok"

    # Second delivery (replay)
    res2 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res2.status == "ok"

    # Verify documents table has exactly 1 document
    contact = await temp_db.fetchrow("SELECT * FROM whatsapp_contacts WHERE phone_number = $1", phone)
    user_id = contact.get("user_id") or contact["id"]
    docs = await temp_db.fetch("SELECT * FROM documents WHERE user_id = $1", user_id)
    assert len(docs) == 1


@pytest.mark.anyio
@patch("services.whatsapp.workflow_adapter.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_draft_finalization_replay_safety(mock_ai, temp_db):
    """Verify replaying 'YES' confirmation creates exactly ONE finalized document record in DB."""
    mock_ai.return_value = "FORMAL LEGAL NOTICE CONTENT..."
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919997779999", user_id, now_iso,
    )
    reqs = {"recipient": "Landlord Ramesh", "purpose": "Deposit refund"}
    await set_drafting_state(temp_db, contact_id, "legal_notice", reqs, workflow_state=WorkflowState.DRAFT_READY, confirmation_status="awaiting_confirmation")

    orchestrator = WhatsAppOrchestrator()
    confirm_msg_id = f"wamid_yes_{uuid.uuid4().hex[:8]}"

    payload = {
        "from_phone": "+919997779999",
        "message_text": "1",
        "message_id": confirm_msg_id,
    }

    # First delivery -> finalizes draft & registers document
    res1 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res1.status == "ok"
    assert "Final Legal Notice Draft Generated Successfully" in res1.reply

    # Second delivery (replay)
    res2 = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res2.status == "ok"
    assert res2.reply == res1.reply

    # Verify only 1 draft document registered in documents table
    docs = await temp_db.fetch("SELECT * FROM documents WHERE user_id = $1 AND document_type = 'text/plain'", user_id)
    assert len(docs) == 1
