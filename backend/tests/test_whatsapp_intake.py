"""
test_whatsapp_intake.py — Step 2C Document Intake & Media Handling Test Suite.

Verifies:
1. DevMediaDownloader media resolution & DownloadedMedia normalization.
2. Valid PDF and Image intake, document DB record creation, and ownership.
3. Content validation, oversized file rejection, MIME mismatch rejection.
4. Filename sanitization (path traversal protection).
5. SSRF protection (rejecting arbitrary external URLs).
6. Multilingual intake confirmations (Marathi, Hindi, English).
"""

import pytest
import uuid
import os
from unittest.mock import AsyncMock, patch
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.media import DevMediaDownloader, DownloadedMedia
from services.whatsapp.document_adapter import process_whatsapp_document_intake, sanitize_filename
from services.whatsapp.repository import get_contact_by_phone
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
async def test_successful_media_download():
    """Verify DevMediaDownloader returns normalized DownloadedMedia payload."""
    downloader = DevMediaDownloader()
    downloaded = await downloader.download_media(media_id="sample_pdf")

    assert isinstance(downloaded, DownloadedMedia)
    assert downloaded.mime_type == "application/pdf"
    assert downloaded.filename == "sample_agreement.pdf"
    assert downloaded.content.startswith(b"%PDF")
    assert downloaded.file_size > 0


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_valid_pdf_intake(mock_analyze, temp_db):
    """Verify valid PDF intake registers document in DB and returns localized confirmation."""
    mock_analyze.return_value = {"summary": {"document_type": "Rental Agreement", "overall_risk": "LOW"}}
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # Send document intake request
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze this contract", "media_url": "sample_pdf"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "sample_agreement.pdf" in res.reply
    assert "Document Analysis Complete" in res.reply or "received successfully" in res.reply

    # Verify DB record creation
    doc = await temp_db.fetchrow("SELECT * FROM documents WHERE filename = 'sample_agreement.pdf'")
    assert doc is not None
    assert doc["document_type"] == "application/pdf"


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_valid_image_intake(mock_analyze, temp_db):
    """Verify valid PNG image intake registers document in DB and returns Marathi confirmation."""
    mock_analyze.return_value = {"summary": {"document_type": "Notice", "overall_risk": "LOW"}}
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in Marathi ('1')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)

    # Send image intake request
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "हा कागदपत्र तपासा", "media_url": "sample_png"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "notice_photo.png" in res.reply
    assert "कागदपत्र विश्लेषण पूर्ण" in res.reply or "यशस्वीपणे प्राप्त" in res.reply

    doc = await temp_db.fetchrow("SELECT * FROM documents WHERE filename = 'notice_photo.png'")
    assert doc is not None
    assert doc["document_type"] == "image/png"


@pytest.mark.anyio
async def test_oversized_file_rejected(temp_db):
    """Verify oversized download payload is rejected with localized error response."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze contract", "media_url": "oversized_trigger"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "File is too large" in res.reply or "10 MB" in res.reply


@pytest.mark.anyio
async def test_ssrf_arbitrary_url_rejected():
    """Verify DevMediaDownloader rejects arbitrary external URLs (SSRF protection)."""
    downloader = DevMediaDownloader()
    with pytest.raises(ValueError, match="Arbitrary external URLs are not permitted"):
        await downloader.download_media(media_id="http://malicious-external-site.com/exploit.pdf")


@pytest.mark.anyio
async def test_path_traversal_filename_sanitized():
    """Verify unsafe path-traversal filenames are sanitized cleanly."""
    unsafe = "../../../etc/passwd"
    safe = sanitize_filename(unsafe)
    assert safe == "passwd"
    assert ".." not in safe
    assert "/" not in safe


@pytest.mark.anyio
async def test_ownership_association(temp_db):
    """Verify document record is associated with the user's account ID."""
    contact_id = f"wac_{uuid.uuid4().hex[:8]}"
    user_id = f"usr_{uuid.uuid4().hex[:8]}"

    await temp_db.execute(
        """
        INSERT INTO whatsapp_contacts (id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, datetime('now'), datetime('now'))
        """,
        contact_id,
        f"+91999{uuid.uuid4().hex[:7]}",
        user_id,
        "en",
        "completed",
    )

    downloader = DevMediaDownloader()
    downloaded = await downloader.download_media("sample_pdf")
    contact = {"id": contact_id, "user_id": user_id}

    doc = await process_whatsapp_document_intake(temp_db, contact, downloaded, "msg_1")

    assert doc["user_id"] == user_id
    db_doc = await temp_db.fetchrow("SELECT * FROM documents WHERE id = $1", doc["id"])
    assert db_doc["user_id"] == user_id


@pytest.mark.anyio
@patch("services.whatsapp.document_analysis_adapter.analyze_legal_document", new_callable=AsyncMock)
async def test_multilingual_intake_confirmations(mock_analyze, temp_db):
    """Verify Marathi, Hindi, and English intake confirmations return localized text."""
    mock_analyze.return_value = {"summary": {"document_type": "Agreement", "overall_risk": "LOW"}}
    orchestrator = WhatsAppOrchestrator()

    # 1. Hindi test ('2')
    phone_hi = f"+91999{uuid.uuid4().hex[:7]}"
    await orchestrator.process_inbound_message({"from_phone": phone_hi, "message_text": "2"}, db=temp_db)
    res_hi = await orchestrator.process_inbound_message(
        {"from_phone": phone_hi, "message_text": "यह नोटिस देखें", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res_hi.status == "ok"
    assert "sample_agreement.pdf" in res_hi.reply
    assert "दस्तावेज़ विश्लेषण पूर्ण" in res_hi.reply or "सफलतापूर्वक प्राप्त" in res_hi.reply

    # 2. Marathi test ('1')
    phone_mr = f"+91999{uuid.uuid4().hex[:7]}"
    await orchestrator.process_inbound_message({"from_phone": phone_mr, "message_text": "1"}, db=temp_db)
    res_mr = await orchestrator.process_inbound_message(
        {"from_phone": phone_mr, "message_text": "हे करारपत्र तपासा", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res_mr.status == "ok"
    assert "sample_agreement.pdf" in res_mr.reply
    assert "कागदपत्र विश्लेषण पूर्ण" in res_mr.reply or "यशस्वीपणे प्राप्त" in res_mr.reply

    # 3. English test ('3')
    phone_en = f"+91999{uuid.uuid4().hex[:7]}"
    await orchestrator.process_inbound_message({"from_phone": phone_en, "message_text": "3"}, db=temp_db)
    res_en = await orchestrator.process_inbound_message(
        {"from_phone": phone_en, "message_text": "Check this contract", "media_url": "sample_pdf"},
        db=temp_db,
    )
    assert res_en.status == "ok"
    assert "sample_agreement.pdf" in res_en.reply
    assert "Document Analysis Complete" in res_en.reply or "received successfully" in res_en.reply


@pytest.mark.anyio
async def test_missing_media_id_rejection():
    """Verify downloader safely rejects empty/missing media IDs."""
    downloader = DevMediaDownloader()
    with pytest.raises(ValueError, match="Missing media ID or reference"):
        await downloader.download_media("", "")


@pytest.mark.anyio
async def test_download_timeout_handling(temp_db):
    """Verify download timeout is caught gracefully and returns friendly error."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze document", "media_url": "timeout_trigger"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "Could not process document" in res.reply or "त्रुटी" in res.reply
    assert "TimeoutError" not in res.reply  # No exception leak to user


@pytest.mark.anyio
async def test_empty_zero_byte_download_rejected(temp_db):
    """Verify zero-byte empty download is rejected without creating a DB document record."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze document", "media_url": "empty_bytes_trigger"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "Could not process document" in res.reply
    # Verify no document record created in DB
    doc_count = await temp_db.fetchrow("SELECT COUNT(*) as count FROM documents WHERE filename = 'empty.pdf'")
    assert doc_count["count"] == 0


@pytest.mark.anyio
async def test_mime_content_mismatch_rejected(temp_db):
    """Verify MIME/content mismatch (fake PDF extension but HTML bytes) is rejected."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Analyze document", "media_url": "mismatch_trigger"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "Could not process document" in res.reply
    doc_count = await temp_db.fetchrow("SELECT COUNT(*) as count FROM documents WHERE filename = 'fake_notice.pdf'")
    assert doc_count["count"] == 0


@pytest.mark.anyio
async def test_downloader_boundary_size_enforcement():
    """Verify 10 MB download size ceiling is enforced directly at the Downloader boundary."""
    downloader = DevMediaDownloader()
    with pytest.raises(ValueError, match="Exceeds size limit"):
        await downloader.download_media("oversized_trigger")


@pytest.mark.anyio
async def test_ownership_isolation_cross_user_denied(temp_db):
    """Verify User A's uploaded document belongs strictly to User A and cannot be accessed by User B."""
    user_a_id = f"usr_a_{uuid.uuid4().hex[:6]}"
    user_b_id = f"usr_b_{uuid.uuid4().hex[:6]}"

    # User A uploads document
    downloader = DevMediaDownloader()
    downloaded = await downloader.download_media("sample_pdf")
    contact_a = {"id": "wac_a", "user_id": user_a_id}

    doc_a = await process_whatsapp_document_intake(temp_db, contact_a, downloaded, "msg_a")

    # Verify DB record is owned by User A
    assert doc_a["user_id"] == user_a_id

    # Verify User B query for User A's document returns nothing under User B's scope
    doc_lookup_b = await temp_db.fetchrow(
        "SELECT * FROM documents WHERE id = $1 AND user_id = $2", doc_a["id"], user_b_id
    )
    assert doc_lookup_b is None

    # User A query succeeds
    doc_lookup_a = await temp_db.fetchrow(
        "SELECT * FROM documents WHERE id = $1 AND user_id = $2", doc_a["id"], user_a_id
    )
    assert doc_lookup_a is not None


@pytest.mark.anyio
async def test_database_failure_no_false_success(temp_db):
    """Verify that if database insert fails, an exception is raised and no false success response is generated."""
    class BrokenDB:
        async def execute(self, query, *args):
            raise RuntimeError("Database connection lost during insert")

    broken_db = BrokenDB()
    downloader = DevMediaDownloader()
    downloaded = await downloader.download_media("sample_pdf")
    contact = {"id": "wac_broken", "user_id": "usr_broken"}

    with pytest.raises(RuntimeError, match="Database connection lost"):
        await process_whatsapp_document_intake(broken_db, contact, downloaded, "msg_err")

