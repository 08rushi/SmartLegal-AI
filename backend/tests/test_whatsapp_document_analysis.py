"""
test_whatsapp_document_analysis.py — Step 2D Document Analysis & Processing State Test Suite.

Verifies:
1. Persistent document processing state machine (pending -> processing -> completed / failed).
2. Concurrency & duplicate analysis prevention (0 duplicate AI calls across parallel requests).
3. Stale job recovery (> 3 minutes threshold).
4. Failed state and explicit user retry behavior.
5. Completed result reuse for document follow-up Q&A (0 re-analysis calls).
6. Multilingual summaries and processing status messages (Marathi, Hindi, English).
7. Cross-user document ownership security isolation.
"""

import pytest
import uuid
import datetime
import json
from unittest.mock import AsyncMock, patch
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.document_analysis_adapter import (
    execute_whatsapp_document_analysis,
    answer_document_followup,
    resolve_document_for_contact,
)
from services.whatsapp.media import DevMediaDownloader
from services.whatsapp.document_adapter import process_whatsapp_document_intake
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture."""
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
        """)
        yield db


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_pdf_document_analysis_success(mock_analyze, temp_db):
    """Verify PDF document intake + analysis returns completed summary in English."""
    mock_analyze.return_value = {
        "summary": {
            "document_type": "Rental Agreement",
            "overall_risk": "LOW",
            "key_provisions": ["11 months lease duration", "Security deposit refund in 30 days"],
        }
    }

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # 1. Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # 2. Upload PDF document & trigger analysis
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze this PDF contract", "media_url": "sample_pdf"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "Document Analysis Complete" in res.reply
    assert "Rental Agreement" in res.reply
    assert "LOW" in res.reply
    assert "Security deposit refund" in res.reply

    # Verify DB persistence
    doc = await temp_db.fetchrow("SELECT * FROM documents WHERE filename = 'sample_agreement.pdf'")
    assert doc["status"] == "completed"

    analysis_row = await temp_db.fetchrow("SELECT * FROM analyses WHERE document_id = $1", doc["id"])
    assert analysis_row is not None
    result = json.loads(analysis_row["result_json"])
    assert result["status"] == "completed"
    mock_analyze.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_duplicate_analysis_prevention(mock_analyze, temp_db):
    """Verify concurrent request for document in 'processing' state returns status response without duplicate AI call."""
    mock_analyze.return_value = {"summary": {"document_type": "Lease", "overall_risk": "MEDIUM"}}

    contact_id = "wac_dup_test"
    user_id = "usr_dup_test"
    doc_id = "doc_dup_123"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Pre-insert document and active 'processing' analysis state
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
        doc_id, user_id, "contract.pdf", "local://contract.pdf", 1000, "processing", now_iso,
    )
    processing_payload = json.dumps({"status": "processing", "started_at": now_iso})
    await temp_db.execute(
        "INSERT INTO analyses (id, document_id, result_json, analyzed_at) VALUES ($1, $2, $3, $4)",
        "ana_1", doc_id, processing_payload, now_iso,
    )

    contact = {"id": contact_id, "user_id": user_id}

    # Execute analysis request while document is currently processing
    reply = await execute_whatsapp_document_analysis(temp_db, contact, document_id=doc_id, language="en")

    assert "currently being analyzed" in reply or "Please wait" in reply
    # Verify AI model was NOT called (0 duplicate calls!)
    mock_analyze.assert_not_called()


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_stale_processing_recovery(mock_analyze, temp_db):
    """Verify document trapped in 'processing' > 3 minutes is recovered as stale and safely re-run."""
    mock_analyze.return_value = {"summary": {"document_type": "Sale Deed", "overall_risk": "LOW"}}

    contact_id = "wac_stale_test"
    user_id = "usr_stale_test"
    doc_id = "doc_stale_123"

    # Pre-insert stale processing state (4 minutes ago)
    stale_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=4)
    stale_iso = stale_dt.isoformat()

    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
        doc_id, user_id, "deed.pdf", "local://deed.pdf", 1000, "processing", stale_iso,
    )
    stale_payload = json.dumps({"status": "processing", "started_at": stale_iso})
    await temp_db.execute(
        "INSERT INTO analyses (id, document_id, result_json, analyzed_at) VALUES ($1, $2, $3, $4)",
        "ana_stale", doc_id, stale_payload, stale_iso,
    )

    contact = {"id": contact_id, "user_id": user_id}

    # Execute analysis request
    reply = await execute_whatsapp_document_analysis(temp_db, contact, document_id=doc_id, language="en")

    assert "Document Analysis Complete" in reply
    assert "Sale Deed" in reply
    mock_analyze.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_failed_state_and_explicit_retry(mock_analyze, temp_db):
    """Verify failed analysis creates 'failed' state, and user explicit retry triggers fresh execution."""
    contact_id = "wac_fail_test"
    user_id = "usr_fail_test"
    doc_id = "doc_fail_123"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
        doc_id, user_id, "notice.pdf", "local://notice.pdf", 1000, "ready", now_iso,
    )

    contact = {"id": contact_id, "user_id": user_id}

    # 1. Simulate AI failure
    mock_analyze.side_effect = RuntimeError("Groq rate limit exceeded")
    fail_reply = await execute_whatsapp_document_analysis(temp_db, contact, document_id=doc_id, language="en")

    assert "couldn't complete the document analysis" in fail_reply
    doc = await temp_db.fetchrow("SELECT status FROM documents WHERE id = $1", doc_id)
    assert doc["status"] == "failed"

    # 2. Simulate User Explicit Retry ("try again" / force_retry=True)
    mock_analyze.side_effect = None
    mock_analyze.return_value = {"summary": {"document_type": "Legal Notice", "overall_risk": "HIGH"}}

    retry_reply = await execute_whatsapp_document_analysis(
        temp_db, contact, document_id=doc_id, language="en", force_retry=True
    )

    assert "Document Analysis Complete" in retry_reply
    assert "Legal Notice" in retry_reply
    doc_after = await temp_db.fetchrow("SELECT status FROM documents WHERE id = $1", doc_id)
    assert doc_after["status"] == "completed"


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_completed_result_reuse_for_followup(mock_analyze, mock_chat, temp_db):
    """Verify follow-up question for completed document reuses cached analysis without re-running full document analysis."""
    mock_analyze.return_value = {"summary": {"document_type": "Agreement", "overall_risk": "LOW"}}
    mock_chat.return_value = "The notice period specified in Clause 4 is 30 days written notice."

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in English
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # 1. Upload & Analyze Document
    await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze document", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert mock_analyze.call_count == 1

    # 2. Ask document-specific follow-up question
    res_followup = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "What is the notice period in this agreement?"},
        db=temp_db,
    )

    assert res_followup.status == "ok"
    assert "30 days written notice" in res_followup.reply
    # Verify mock_analyze was NOT called a second time (0 re-analysis calls!)
    assert mock_analyze.call_count == 1
    mock_chat.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_multilingual_document_analysis(mock_analyze, temp_db):
    """Verify Marathi and Hindi document analysis responses return localized text."""
    mock_analyze.return_value = {
        "summary": {
            "document_type": "घरभाडे करार",
            "overall_risk": "मध्यम",
            "key_provisions": ["11 महिने कालावधी", "डिपॉझिट परत करण्याची अट"],
        }
    }

    orchestrator = WhatsAppOrchestrator()

    # 1. Marathi ('1')
    phone_mr = f"+91999{uuid.uuid4().hex[:7]}"
    await orchestrator.process_inbound_message({"from_phone": phone_mr, "message_text": "1"}, db=temp_db)
    res_mr = await orchestrator.process_inbound_message(
        {"from_phone": phone_mr, "message_text": "या कराराचे विश्लेषण करा", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res_mr.status == "ok"
    assert "कागदपत्र विश्लेषण पूर्ण" in res_mr.reply
    assert "एकूण धोका पातळी" in res_mr.reply

    # 2. Hindi ('2')
    phone_hi = f"+91999{uuid.uuid4().hex[:7]}"
    await orchestrator.process_inbound_message({"from_phone": phone_hi, "message_text": "2"}, db=temp_db)
    res_hi = await orchestrator.process_inbound_message(
        {"from_phone": phone_hi, "message_text": "इस दस्तावेज़ का विश्लेषण करें", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res_hi.status == "ok"
    assert "दस्तावेज़ विश्लेषण पूर्ण" in res_hi.reply
    assert "कुल जोखिम स्तर" in res_hi.reply


@pytest.mark.anyio
async def test_cross_user_document_analysis_denied(temp_db):
    """Verify User B cannot analyze or query User A's uploaded document."""
    user_a_id = f"usr_a_{uuid.uuid4().hex[:6]}"
    user_b_id = f"usr_b_{uuid.uuid4().hex[:6]}"
    doc_id = "doc_secret_a"

    # User A uploads document
    await temp_db.execute(
        "INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at) VALUES ($1, $2, $3, $4, $5, $6, datetime('now'))",
        doc_id, user_a_id, "private.pdf", "local://private.pdf", 500, "ready",
    )

    contact_b = {"id": "wac_b", "user_id": user_b_id}

    # User B attempts to analyze User A's doc_id
    reply = await execute_whatsapp_document_analysis(temp_db, contact_b, document_id=doc_id, language="en")

    assert "No document found to analyze" in reply
    doc_b_check = await resolve_document_for_contact(temp_db, contact_b, document_id=doc_id)
    assert doc_b_check is None
