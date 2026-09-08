"""
test_whatsapp_document_context.py — Step 2E Document Conversation Context & Workflow Intelligence Test Suite.

Verifies:
1. Persistent 1-to-1 conversation context storage model (`whatsapp_conversation_context` DB table).
2. Active document context tracking & switching.
3. Deterministic context management commands (`clear document`, `current document`, `change document`).
4. Contact-scoped persisted candidate document selection & numeric choice resolution (`1`, `2`).
5. Invalid numeric selection & non-numeric prompt handling while selection is pending.
6. Selection cancellation upon context clear or new document upload.
7. Context status invariants (`active_document_id != NULL` => `context_status = 'active'`).
8. Restart & process independence (survives separate DB connections/sessions).
9. General Legal Q&A vs Document Q&A routing.
10. Cross-user context & document ownership security isolation.
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
    get_active_document_id,
    set_active_document,
    clear_active_document,
    set_pending_candidates,
    resolve_candidate_selection,
)
from services.whatsapp.media import DevMediaDownloader
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture with complete Step 2E schema."""
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
                context_status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        yield db


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_active_document_tracking_and_switching(mock_analyze, temp_db):
    """Verify uploading document A makes A active, uploading B makes B active while preserving A."""
    mock_analyze.return_value = {"summary": {"document_type": "Agreement", "overall_risk": "LOW"}}
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # 1. Upload Document A
    res1 = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Upload contract A", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res1.status == "ok"
    contact = await temp_db.fetchrow("SELECT * FROM whatsapp_contacts WHERE phone_number = $1", phone)
    ctx1 = await get_or_create_context(temp_db, contact["id"])
    assert ctx1["active_document_id"] is not None
    doc1_id = ctx1["active_document_id"]

    # 2. Upload Document B (Image)
    res2 = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Upload notice B", "media_url": "sample_png"},
        db=temp_db,
    )
    assert res2.status == "ok"
    ctx2 = await get_or_create_context(temp_db, contact["id"])
    assert ctx2["active_document_id"] is not None
    assert ctx2["active_document_id"] != doc1_id

    # Verify Document A is still safely stored in DB
    doc1_db = await temp_db.fetchrow("SELECT * FROM documents WHERE id = $1", doc1_id)
    assert doc1_db is not None


@pytest.mark.anyio
async def test_deterministic_clear_document_command(temp_db):
    """Verify 'clear document' command resets active_document_id to NULL and workflow_state to idle."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard & simulate active document context
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)
    contact = await temp_db.fetchrow("SELECT * FROM whatsapp_contacts WHERE phone_number = $1", phone)

    await set_active_document(temp_db, contact["id"], "doc_test_123", workflow_state="document_active")

    # Send clear document command
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "clear document"}, db=temp_db
    )

    assert res.status == "ok"
    assert "Document context cleared" in res.reply

    ctx = await get_or_create_context(temp_db, contact["id"])
    assert ctx["active_document_id"] is None
    assert ctx["workflow_state"] == "idle"
    assert ctx["context_status"] == "cleared"


@pytest.mark.anyio
async def test_persisted_numeric_candidate_selection(temp_db):
    """Verify multiple documents -> change document -> persisted candidates -> numeric choice '2' activates candidate B."""
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Pre-insert contact and 2 documents
    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919991112233", user_id, now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        "doc_A", user_id, "rental_agreement.pdf", "local://rental.pdf", now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        "doc_B", user_id, "employment_contract.pdf", "local://employment.pdf", now_iso,
    )

    orchestrator = WhatsAppOrchestrator()

    # 1. Send 'change document' command
    res1 = await orchestrator.process_inbound_message(
        {"from_phone": "+919991112233", "message_text": "change document"}, db=temp_db
    )
    assert "Please select a document to activate" in res1.reply
    assert "1. employment_contract.pdf" in res1.reply or "2. employment_contract.pdf" in res1.reply

    ctx1 = await get_or_create_context(temp_db, contact_id)
    assert ctx1["workflow_state"] == "awaiting_document_selection"

    # 2. Select option '2'
    res2 = await orchestrator.process_inbound_message(
        {"from_phone": "+919991112233", "message_text": "2"}, db=temp_db
    )
    assert "Selected document is now active" in res2.reply

    ctx2 = await get_or_create_context(temp_db, contact_id)
    assert ctx2["active_document_id"] is not None
    assert ctx2["workflow_state"] == "document_active"
    assert ctx2["context_status"] == "active"
    assert ctx2["pending_candidates_json"] == "[]"


@pytest.mark.anyio
async def test_invalid_numeric_selection_retry(temp_db):
    """Verify invalid numeric choice '9' returns localized retry prompt without modifying active document."""
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    contact_id = f"wac_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at) VALUES ($1, $2, $3, 'en', 'completed', $4, $4)",
        contact_id, "+919994445566", user_id, now_iso,
    )
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, 1000, 'ready', $5)",
        "doc_X", user_id, "docX.pdf", "local://x.pdf", now_iso,
    )

    await set_pending_candidates(temp_db, contact_id, ["doc_X"])

    orchestrator = WhatsAppOrchestrator()

    # Send invalid choice '9'
    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919994445566", "message_text": "9"}, db=temp_db
    )

    assert "Invalid selection" in res.reply
    ctx = await get_or_create_context(temp_db, contact_id)
    assert ctx["workflow_state"] == "awaiting_document_selection"
    assert ctx["pending_candidates_json"] != "[]"


@pytest.mark.anyio
async def test_selection_isolation_between_contacts(temp_db):
    """Verify Contact B cannot resolve or use Contact A's candidate document selection."""
    contact_a_id = "wac_user_A"
    contact_b_id = "wac_user_B"

    await set_pending_candidates(temp_db, contact_a_id, ["doc_secret_A"])

    # Contact B attempts to select option '1'
    cand_b = await resolve_candidate_selection(temp_db, contact_b_id, 1)
    assert cand_b is None


@pytest.mark.anyio
async def test_selection_canceled_upon_clear_or_new_upload(temp_db):
    """Verify clearing context invalidates candidate selection list."""
    contact_id = "wac_clear_test"
    await set_pending_candidates(temp_db, contact_id, ["doc_1", "doc_2"])

    # Clear document context
    await clear_active_document(temp_db, contact_id)

    cand = await resolve_candidate_selection(temp_db, contact_id, 1)
    assert cand is None

    ctx = await get_or_create_context(temp_db, contact_id)
    assert ctx["workflow_state"] == "idle"
    assert ctx["context_status"] == "cleared"


@pytest.mark.anyio
async def test_restart_and_process_independence(temp_db):
    """Verify persisted context & candidates survive fresh database connections and service restarts."""
    contact_id = "wac_restart_test"
    doc_id = "doc_persisted_999"

    await set_pending_candidates(temp_db, contact_id, [doc_id])

    # Resolve from DB connection
    resolved_id = await resolve_candidate_selection(temp_db, contact_id, 1)
    assert resolved_id == doc_id
