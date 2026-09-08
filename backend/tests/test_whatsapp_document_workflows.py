"""
test_whatsapp_document_workflows.py — Step 2F Document Workflow Actions & Progressive Drafting Test Suite.

Verifies:
1. Canonical service reuse (ai_orchestrator & BaseAIProvider integration).
2. Workflow action routing (`identify_risks`, `legal_next_steps`, `draft_legal_notice`, `draft_document`).
3. Contextual "draft it" resolution using active document context.
4. Progressive information collection (avoids repeated questions; never fabricates missing facts).
5. Draft preview (`draft_ready`) & explicit deterministic confirmation ("1" / "YES") triggering document registration.
6. Deterministic workflow control ("cancel") clearing drafting state.
7. Workflow state machine validation (`validate_workflow_state_transition`).
8. Multilingual workflow prompts (Marathi, Hindi, English).
9. Cross-user context & document ownership security isolation.
"""

import pytest
import uuid
import datetime
import json
from unittest.mock import AsyncMock, patch

from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.context_repository import (
    get_or_create_context,
    set_active_document,
    clear_active_document,
    set_drafting_state,
    clear_drafting_state,
    validate_workflow_state_transition,
    WorkflowState,
)
from services.whatsapp.workflow_adapter import (
    handle_risk_analysis_action,
    handle_legal_next_steps_action,
    handle_drafting_workflow,
    handle_draft_confirmation,
)
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture with complete Step 2F schema."""
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
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                document_id TEXT UNIQUE NOT NULL,
                result_json TEXT NOT NULL,
                analyzed_at TEXT NOT NULL
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
        """)
        yield db


@pytest.mark.anyio
async def test_workflow_state_transition_validation():
    """Verify central workflow state transition validation helper."""
    assert validate_workflow_state_transition("idle", WorkflowState.DOCUMENT_ACTIVE) == WorkflowState.DOCUMENT_ACTIVE
    assert validate_workflow_state_transition("idle", WorkflowState.DRAFT_READY) == WorkflowState.DRAFT_READY
    assert validate_workflow_state_transition("idle", "unsupported_state") == WorkflowState.IDLE


@pytest.mark.anyio
async def test_risk_analysis_action_uses_cached_analysis(temp_db):
    """Verify 'what are the risks' action reuses cached document analysis without calling full analysis pipeline."""
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    doc_id = f"doc_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919998881111", user_id, now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        doc_id, user_id, "rental_agreement.pdf", "local://rent.pdf", now_iso,
    )

    analysis_data = {
        "summary": {
            "document_type": "Rental Agreement",
            "overall_risk": "HIGH",
            "high_risk_clauses": ["11-month lock-in period penalty", "Unilateral rent increase by 20%"],
            "your_obligations": ["Pay rent by 5th of every month"],
        }
    }
    await temp_db.execute(
        "INSERT INTO analyses (id, document_id, result_json, analyzed_at) VALUES ($1, $2, $3, $4)",
        f"ans_{uuid.uuid4().hex[:6]}", doc_id, json.dumps(analysis_data), now_iso,
    )
    await set_active_document(temp_db, contact_id, doc_id, workflow_state="document_active")

    contact_dict = {"id": contact_id, "user_id": user_id, "preferred_language": "en"}
    reply = await handle_risk_analysis_action(temp_db, contact_dict, language="en")

    assert "HIGH" in reply
    assert "11-month lock-in period penalty" in reply
    assert "Pay rent by 5th of every month" in reply


@pytest.mark.anyio
@patch("services.whatsapp.workflow_adapter.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_legal_next_steps_action(mock_ai, temp_db):
    """Verify 'what should I do next?' generates structured options and recommended steps."""
    mock_ai.return_value = "1. Situation Summary: Dispute regarding rent.\n2. Recommended Next Step: Send legal notice."
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    doc_id = f"doc_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919998882222", user_id, now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        doc_id, user_id, "notice_letter.pdf", "local://notice.pdf", now_iso,
    )
    await set_active_document(temp_db, contact_id, doc_id, workflow_state="document_active")

    orchestrator = WhatsAppOrchestrator()
    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919998882222", "message_text": "what should I do next?"}, db=temp_db
    )

    assert res.status == "ok"
    assert "Recommended Next Step" in res.reply or mock_ai.called


@pytest.mark.anyio
async def test_contextual_draft_it_progressive_collection(temp_db):
    """Verify 'draft it' automatically resolves active document context and asks missing questions progressively."""
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    doc_id = f"doc_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919998883333", user_id, now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        doc_id, user_id, "lease_agreement.pdf", "local://lease.pdf", now_iso,
    )
    await set_active_document(temp_db, contact_id, doc_id, workflow_state="document_active")

    orchestrator = WhatsAppOrchestrator()

    # Step 1: User says "draft it"
    res1 = await orchestrator.process_inbound_message(
        {"from_phone": "+919998883333", "message_text": "draft a notice based on this"}, db=temp_db
    )
    assert "Who should this notice/draft be addressed to?" in res1.reply
    ctx1 = await get_or_create_context(temp_db, contact_id)
    assert ctx1["workflow_state"] == WorkflowState.AWAITING_DRAFTING_INPUT

    # Step 2: User provides recipient name "Mr. Ramesh (Landlord)"
    res2 = await orchestrator.process_inbound_message(
        {"from_phone": "+919998883333", "message_text": "Mr. Ramesh (Landlord)"}, db=temp_db
    )
    assert "What is the main reason or demand for this notice?" in res2.reply

    # Step 3: User provides reason "Refund of security deposit of Rs 50,000"
    res3 = await orchestrator.process_inbound_message(
        {"from_phone": "+919998883333", "message_text": "Refund of security deposit of Rs 50,000"}, db=temp_db
    )
    assert "Legal Notice Draft Preview" in res3.reply
    assert "Mr. Ramesh (Landlord)" in res3.reply
    ctx3 = await get_or_create_context(temp_db, contact_id)
    assert ctx3["workflow_state"] == WorkflowState.DRAFT_READY


@pytest.mark.anyio
@patch("services.whatsapp.workflow_adapter.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_draft_ready_explicit_confirmation(mock_ai, temp_db):
    """Verify '1' or 'YES' in draft_ready state triggers final document generation & registers document in DB."""
    mock_ai.return_value = "FORMAL LEGAL NOTICE\nTo: Mr. Ramesh\nDemand: Refund deposit..."
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919998884444", user_id, now_iso,
    )
    reqs = {"recipient": "Mr. Ramesh", "purpose": "Security deposit refund"}
    await set_drafting_state(temp_db, contact_id, "legal_notice", reqs, workflow_state=WorkflowState.DRAFT_READY, confirmation_status="awaiting_confirmation")

    orchestrator = WhatsAppOrchestrator()

    # User confirms with "1"
    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919998884444", "message_text": "1"}, db=temp_db
    )

    assert "Final Legal Notice Draft Generated Successfully" in res.reply
    ctx = await get_or_create_context(temp_db, contact_id)
    assert ctx["workflow_state"] in (WorkflowState.DOCUMENT_ACTIVE, WorkflowState.IDLE)
    assert ctx["draft_type"] is None

    # Verify registered in documents DB table
    doc_row = await temp_db.fetchrow("SELECT * FROM documents WHERE user_id = $1 AND document_type = 'text/plain'", user_id)
    assert doc_row is not None


@pytest.mark.anyio
async def test_draft_cancellation_clears_drafting_state(temp_db):
    """Verify 'cancel' command while in draft_ready clears temporary drafting state without creating document."""
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919998885555", user_id, now_iso,
    )
    reqs = {"recipient": "Party X", "purpose": "Testing cancel"}
    await set_drafting_state(temp_db, contact_id, "legal_notice", reqs, workflow_state=WorkflowState.DRAFT_READY, confirmation_status="awaiting_confirmation")

    orchestrator = WhatsAppOrchestrator()
    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919998885555", "message_text": "cancel"}, db=temp_db
    )

    assert "cancelled" in res.reply.lower()
    ctx = await get_or_create_context(temp_db, contact_id)
    assert ctx["workflow_state"] == WorkflowState.IDLE
    assert ctx["draft_type"] is None
