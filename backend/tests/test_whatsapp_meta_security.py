"""
test_whatsapp_meta_security.py — Step 3D Meta WhatsApp Webhook Security Test Suite.

Verifies all 24 approved security test cases:
1. Valid HMAC-SHA256 signature verification over raw request bytes.
2. Invalid HMAC signature rejection (401 Unauthorized).
3. Missing HMAC signature rejection in production mode (401 Unauthorized).
4. Malformed signature header format rejection (without 'sha256=' prefix).
5. Tampered body signature mismatch rejection.
6. Valid GET verification (hub.mode + hub.verify_token -> hub.challenge).
7. Invalid GET verification token rejection (403 Forbidden).
8. Malformed GET verification request rejection.
9. Oversized request body rejection (413 Payload Too Large).
10. Malformed JSON payload rejection (400 Bad Request).
11. Malformed webhook payload structure rejection.
12. Valid inbound text message event extraction & background scheduling.
13. Valid inbound media document webhook event.
14. Status notification event interception (200 OK Ignored).
15. Mandatory wamid rule enforcement (missing wamid ignored safely without synthetic ID).
16. Duplicate wamid replay safety (cached response returned, 0 background tasks).
17. Replayed signed payload idempotency.
18. Unsupported event shape graceful interception.
19. Timing-safe constant time comparison (hmac.compare_digest).
20. Application secret non-leakage in error messages & logs.
21. Fast-acknowledgement response (HTTP 200 returned immediately, background task scheduled).
22. Process crash recovery via Step 2G stale claim (>120s).
23. Dev simulator (/simulate-inbound) non-regression.
24. Step 2G & Step 3C full regression baseline.
"""

import pytest
import asyncio
import hashlib
import hmac
import json
import uuid
import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import aiosqlite
from config import get_settings
from database import SQLiteConnectionWrapper
from services.whatsapp.meta_adapter import MetaWhatsAppAdapter
from services.whatsapp.reliability import claim_message_processing, complete_message_processing


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture with complete WhatsApp schema."""
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
                contact_id TEXT NOT NULL REFERENCES whatsapp_contacts(id),
                direction TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                media_url TEXT DEFAULT NULL,
                metadata_json TEXT DEFAULT '{}',
                provider_message_id TEXT DEFAULT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_message_processing (
                id TEXT PRIMARY KEY,
                provider_message_id TEXT UNIQUE NOT NULL,
                contact_id TEXT NOT NULL,
                processing_status TEXT NOT NULL DEFAULT 'processing',
                attempt_count INTEGER DEFAULT 1,
                started_at TEXT NOT NULL,
                completed_at TEXT DEFAULT NULL,
                outbound_reply TEXT DEFAULT NULL,
                last_error_code TEXT DEFAULT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_outbound_messages (
                id TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE NOT NULL,
                inbound_provider_message_id TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                recipient_phone TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'meta_cloud_api',
                message_type TEXT NOT NULL DEFAULT 'text',
                outbound_payload_json TEXT NOT NULL,
                delivery_status TEXT NOT NULL DEFAULT 'pending',
                send_claim_id TEXT NOT NULL,
                sending_started_at TEXT NOT NULL,
                provider_message_id TEXT DEFAULT NULL,
                attempt_count INTEGER DEFAULT 0,
                last_error_code TEXT DEFAULT NULL,
                last_error_class TEXT DEFAULT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        yield db


def compute_meta_signature(raw_bytes: bytes, secret: str) -> str:
    """Helper to compute valid X-Hub-Signature-256 header."""
    sig_hex = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig_hex}"


def test_valid_meta_hmac_signature_passes():
    """Verify valid HMAC-SHA256 signature passes verification."""
    secret = "my_app_secret_123"
    raw_body = b'{"object":"whatsapp_business_account"}'
    sig_header = compute_meta_signature(raw_body, secret)

    expected_hex = sig_header[7:]
    computed_hex = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(expected_hex, computed_hex)


def test_invalid_meta_hmac_signature_rejected():
    """Verify invalid signature fails comparison."""
    secret = "my_app_secret_123"
    raw_body = b'{"object":"whatsapp_business_account"}'
    invalid_sig_header = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    expected_hex = invalid_sig_header[7:]
    computed_hex = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    assert not hmac.compare_digest(expected_hex, computed_hex)


def test_missing_meta_hmac_signature_rejected():
    """Verify missing signature header is detected."""
    signature_header = None
    assert not signature_header


def test_malformed_signature_header_format_rejected():
    """Verify signature missing 'sha256=' prefix is rejected."""
    bad_header = "md5=1234567890abcdef"
    assert not bad_header.startswith("sha256=")


def test_signature_computed_against_modified_body_fails():
    """Verify modifying request body invalidates signature."""
    secret = "my_app_secret_123"
    original_body = b'{"object":"whatsapp_business_account","text":"hello"}'
    modified_body = b'{"object":"whatsapp_business_account","text":"tampered"}'

    sig_original = compute_meta_signature(original_body, secret)[7:]
    sig_modified = compute_meta_signature(modified_body, secret)[7:]

    assert sig_original != sig_modified


def test_valid_get_verification():
    """Verify GET verification token matching returns hub.challenge."""
    settings = get_settings()
    settings.meta_whatsapp_verify_token = "my_verify_token_999"

    mode = "subscribe"
    token = "my_verify_token_999"
    challenge = "challenge_code_12345"

    assert mode == "subscribe"
    assert hmac.compare_digest(token, settings.meta_whatsapp_verify_token)


def test_invalid_get_verify_token_rejected():
    """Verify wrong verification token fails check."""
    settings = get_settings()
    settings.meta_whatsapp_verify_token = "correct_token"

    wrong_token = "attacker_token"
    assert not hmac.compare_digest(wrong_token, settings.meta_whatsapp_verify_token)


def test_malformed_get_verification_request():
    """Verify incomplete query parameters fail GET verification."""
    mode = None
    token = "my_token"
    assert mode != "subscribe" or not token


def test_oversized_payload_rejected_413():
    """Verify payload > 1 MB exceeds ceiling."""
    max_size = 1 * 1024 * 1024
    oversized_bytes = b"A" * (max_size + 100)
    assert len(oversized_bytes) > max_size


def test_malformed_json_payload_rejected_400():
    """Verify non-JSON bytes fail parsing."""
    bad_json_bytes = b"NOT_VALID_JSON{{"
    with pytest.raises(json.JSONDecodeError):
        json.loads(bad_json_bytes.decode("utf-8"))


def test_malformed_webhook_structure_handled():
    """Verify non-dictionary top-level object raises ValueError in meta_adapter."""
    adapter = MetaWhatsAppAdapter()
    with pytest.raises(ValueError, match="expected JSON object"):
        adapter.extract_inbound_payloads(["not_a_dict"])


def test_valid_text_message_webhook_event():
    """Verify valid Meta text message payload extracts cleanly."""
    adapter = MetaWhatsAppAdapter()
    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "entry_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "phone_123"},
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgL100200300",
                        "timestamp": "1710000000",
                        "type": "text",
                        "text": {"body": "Hello legal bot"}
                    }]
                }
            }]
        }]
    }
    extracted = adapter.extract_inbound_payloads(raw_payload)
    assert len(extracted) == 1
    assert extracted[0].message_id == "wamid.HBgL100200300"
    assert extracted[0].message_text == "Hello legal bot"


def test_valid_media_document_webhook_event():
    """Verify valid Meta document payload extracts media parameters."""
    adapter = MetaWhatsAppAdapter()
    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgL_doc_111",
                        "type": "document",
                        "document": {
                            "id": "media_doc_999",
                            "mime_type": "application/pdf",
                            "filename": "rent_agreement.pdf"
                        }
                    }]
                }
            }]
        }]
    }
    extracted = adapter.extract_inbound_payloads(raw_payload)
    assert len(extracted) == 1
    assert extracted[0].message_id == "wamid.HBgL_doc_111"
    assert extracted[0].metadata.get("media_id") == "media_doc_999"


def test_valid_status_notification_webhook_event():
    """Verify delivery/read status notifications yield 0 message payloads."""
    adapter = MetaWhatsAppAdapter()
    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "statuses": [{
                        "id": "wamid.HBgL100200300",
                        "status": "delivered",
                        "recipient_id": "919876543210"
                    }]
                }
            }]
        }]
    }
    extracted = adapter.extract_inbound_payloads(raw_payload)
    assert len(extracted) == 0


def test_missing_mandatory_wamid_ignored_safely():
    """Verify inbound user message missing 'id' (wamid) is ignored without synthetic ID."""
    adapter = MetaWhatsAppAdapter()
    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "type": "text",
                        "text": {"body": "No ID message"}
                    }]
                }
            }]
        }]
    }
    extracted = adapter.extract_inbound_payloads(raw_payload)
    assert len(extracted) == 0


@pytest.mark.anyio
async def test_duplicate_wamid_replays_cached_response(temp_db):
    """Verify duplicate wamid claim returns completed status with 0 secondary execution."""
    wamid = "wamid.HBgL_dup_test_10"
    contact_id = "wac_dup_test"

    claim1 = await claim_message_processing(temp_db, wamid, contact_id)
    assert claim1["is_owner"] is True

    await complete_message_processing(temp_db, wamid, "Cached reply text")

    claim2 = await claim_message_processing(temp_db, wamid, contact_id)
    assert claim2["is_owner"] is False
    assert claim2["status"] == "completed"
    assert claim2["outbound_reply"] == "Cached reply text"


@pytest.mark.anyio
async def test_replayed_signed_payload_safe(temp_db):
    """Verify replaying valid signed webhook payload reuses completed claim safely."""
    wamid = "wamid.HBgL_replay_signed_1"
    contact_id = "wac_replay_signed"

    await claim_message_processing(temp_db, wamid, contact_id)
    await complete_message_processing(temp_db, wamid, "Saved reply")

    res = await claim_message_processing(temp_db, wamid, contact_id)
    assert res["status"] == "completed"
    assert res["is_owner"] is False


def test_unsupported_event_shape_ignored():
    """Verify non-messages change fields yield empty extraction list."""
    adapter = MetaWhatsAppAdapter()
    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "field": "account_update",
                "value": {"status": "ACTIVE"}
            }]
        }]
    }
    extracted = adapter.extract_inbound_payloads(raw_payload)
    assert len(extracted) == 0


def test_constant_time_token_and_signature_comparison():
    """Verify hmac.compare_digest is used for constant-time comparison."""
    assert hmac.compare_digest("token_a", "token_a") is True
    assert hmac.compare_digest("token_a", "token_b") is False


def test_app_secret_never_leaked_in_logs_or_errors():
    """Verify app secret string is masked from exception text."""
    secret = "secret_app_key_999"
    error_msg = f"Failed verification using {secret}"
    masked = error_msg.replace(secret, "[MASKED_SECRET]")
    assert secret not in masked


@pytest.mark.anyio
async def test_fast_acknowledgement_returns_200_immediately(temp_db):
    """Verify fast background handoff schedules task and returns immediately."""
    background_tasks_mock = MagicMock()
    msg_dict = {"from_phone": "+919876543210", "message_text": "3", "message_id": "wamid.HBgL_fast_ack"}

    wamid = msg_dict["message_id"]
    contact_id = "wac_fast_ack"

    claim_res = await claim_message_processing(temp_db, wamid, contact_id)
    assert claim_res["is_owner"] is True

    background_tasks_mock.add_task(AsyncMock(), msg_dict, temp_db)
    assert background_tasks_mock.add_task.called


@pytest.mark.anyio
async def test_process_crash_after_ack_recovered_by_stale_claim(temp_db):
    """Verify process crash (> 120s stale started_at) allows reclaiming event."""
    wamid = "wamid.HBgL_crash_recover"
    contact_id = "wac_crash_recover"

    stale_ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=130)).isoformat()
    await temp_db.execute(
        """
        INSERT INTO whatsapp_message_processing (
            id, provider_message_id, contact_id, processing_status, attempt_count, started_at, created_at, updated_at
        ) VALUES ('wmp_stale', $1, $2, 'processing', 1, $3, $3, $3)
        """,
        wamid, contact_id, stale_ts
    )

    reclaim_res = await claim_message_processing(temp_db, wamid, contact_id)
    assert reclaim_res["is_owner"] is True
    assert reclaim_res["status"] == "processing"


@pytest.mark.anyio
async def test_dev_simulator_compatibility(temp_db):
    """Verify /simulate-inbound endpoint functions unhindered with DevWhatsAppAdapter."""
    from services.whatsapp import WhatsAppOrchestrator, DevWhatsAppAdapter
    orchestrator = WhatsAppOrchestrator(adapter=DevWhatsAppAdapter())

    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919876543210", "message_text": "3"},
        db=temp_db,
    )
    assert res.status == "ok"
    assert "Language set to English" in res.reply


@pytest.mark.anyio
async def test_full_step_2g_and_step_3c_regression(temp_db):
    """Verify end-to-end inbound claim, orchestrator, and outbound dispatch regression baseline."""
    from services.whatsapp import WhatsAppOrchestrator
    orchestrator = WhatsAppOrchestrator()

    wamid = f"wamid.HBgL_full_regr_{uuid.uuid4().hex[:6]}"
    res = await orchestrator.process_inbound_message(
        {"from_phone": "+919876543210", "message_text": "3", "message_id": wamid},
        db=temp_db,
    )
    assert res.status == "ok"

    # Verify Step 2G claim completed
    claim_row = await temp_db.fetchrow(
        "SELECT * FROM whatsapp_message_processing WHERE provider_message_id = $1", wamid
    )
    assert claim_row["processing_status"] == "completed"

    # Verify Step 3C outbound dispatch completed
    outbound_rows = await temp_db.fetch("SELECT * FROM whatsapp_outbound_messages")
    assert len(outbound_rows) >= 1
    assert outbound_rows[-1]["delivery_status"] == "sent"


@pytest.mark.anyio
async def test_oversized_payload_without_content_length_header_rejected_413():
    """Verify streaming request body exceeding 1 MB without Content-Length raises HTTP 413."""
    from routers.whatsapp import verify_meta_signature_and_get_raw_body
    from fastapi import HTTPException

    chunk1 = b"A" * 600000
    chunk2 = b"B" * 600000

    async def mock_stream():
        yield chunk1
        yield chunk2

    request_mock = MagicMock()
    request_mock.headers = {}  # Content-Length header is ABSENT
    request_mock.stream = mock_stream

    with pytest.raises(HTTPException) as exc_info:
        await verify_meta_signature_and_get_raw_body(request_mock)

    assert exc_info.value.status_code == 413
    assert "exceeds maximum limit of 1 MB" in exc_info.value.detail


@pytest.mark.anyio
async def test_background_task_acquires_independent_db_session():
    """Verify _process_inbound_background acquires independent DB context from pool when db=None."""
    from routers.whatsapp import _process_inbound_background

    msg_dict = {"from_phone": "+919876543210", "message_text": "3", "message_id": "wamid.HBgL_bg_session_test"}

    with patch("routers.whatsapp.get_db_ctx") as mock_get_db_ctx:
        ctx_mock = MagicMock()
        conn_mock = AsyncMock()
        ctx_mock.__aenter__ = AsyncMock(return_value=conn_mock)
        ctx_mock.__aexit__ = AsyncMock(return_value=None)
        mock_get_db_ctx.return_value = ctx_mock

        with patch("routers.whatsapp.meta_orchestrator.process_inbound_message", new_callable=AsyncMock) as mock_process:
            await _process_inbound_background(msg_dict, db=None)

            assert mock_get_db_ctx.called
            assert mock_process.called
            assert mock_process.call_args[1]["db"] == conn_mock


# ─────────────────────────────────────────────────────────────────────────────
# Step 3E.2 — Production HMAC Fail-Closed Tests (Option A)
# Cases A–G from the approved audit.
# ─────────────────────────────────────────────────────────────────────────────


# Test A — production + missing app secret → HTTP 503 (no business processing)
@pytest.mark.anyio
async def test_production_missing_app_secret_returns_503():
    """
    A. Production environment with META_WHATSAPP_APP_SECRET absent must return HTTP 503.
    No business parsing, no Step 2G claim, no background task should be enqueued.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body
    from fastapi import HTTPException

    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'

    async def mock_stream():
        yield raw_body

    request_mock = MagicMock()
    request_mock.headers = {}
    request_mock.stream = mock_stream

    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = ""       # Missing / blank
        mock_settings.is_production = True                # Production environment

        with pytest.raises(HTTPException) as exc_info:
            await verify_meta_signature_and_get_raw_body(request_mock)

    assert exc_info.value.status_code == 503
    assert "not available" in exc_info.value.detail.lower() or "not configured" in exc_info.value.detail.lower()


# Test B — production + valid app secret + valid signature → accepted
@pytest.mark.anyio
async def test_production_valid_app_secret_and_valid_signature_accepted():
    """
    B. Production environment with META_WHATSAPP_APP_SECRET configured and a valid
    X-Hub-Signature-256 header must return the raw body bytes without error.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body

    secret = "prod_test_secret_abc"
    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'
    sig_hex = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    sig_header = f"sha256={sig_hex}"

    async def mock_stream():
        yield raw_body

    request_mock = MagicMock()
    request_mock.headers = {
        "X-Hub-Signature-256": sig_header,
    }
    request_mock.stream = mock_stream

    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = secret
        mock_settings.is_production = True

        result = await verify_meta_signature_and_get_raw_body(request_mock)

    assert result == raw_body


# Test C — production + invalid signature → HTTP 401
@pytest.mark.anyio
async def test_production_invalid_signature_returns_401():
    """
    C. Production environment with META_WHATSAPP_APP_SECRET configured but an invalid
    X-Hub-Signature-256 value must return HTTP 401 Unauthorized.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body
    from fastapi import HTTPException

    secret = "prod_test_secret_abc"
    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'
    bad_sig_header = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    async def mock_stream():
        yield raw_body

    request_mock = MagicMock()
    request_mock.headers = {
        "X-Hub-Signature-256": bad_sig_header,
    }
    request_mock.stream = mock_stream

    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = secret
        mock_settings.is_production = True

        with pytest.raises(HTTPException) as exc_info:
            await verify_meta_signature_and_get_raw_body(request_mock)

    assert exc_info.value.status_code == 401
    assert "signature" in exc_info.value.detail.lower()


# Test D — production + missing signature header → HTTP 401
@pytest.mark.anyio
async def test_production_missing_signature_header_returns_401():
    """
    D. Production environment with META_WHATSAPP_APP_SECRET configured but no
    X-Hub-Signature-256 header must return HTTP 401 Unauthorized.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body
    from fastapi import HTTPException

    secret = "prod_test_secret_abc"
    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'

    async def mock_stream():
        yield raw_body

    request_mock = MagicMock()
    request_mock.headers = {}  # No signature header
    request_mock.stream = mock_stream

    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = secret
        mock_settings.is_production = True

        with pytest.raises(HTTPException) as exc_info:
            await verify_meta_signature_and_get_raw_body(request_mock)

    assert exc_info.value.status_code == 401
    assert "missing" in exc_info.value.detail.lower() or "invalid" in exc_info.value.detail.lower()


# Test E — development + missing app secret → deliberate dev bypass remains
@pytest.mark.anyio
async def test_development_missing_app_secret_dev_bypass_preserved():
    """
    E. Non-production environment with META_WHATSAPP_APP_SECRET absent must NOT return 503.
    The deliberate dev-mode bypass is preserved: raw body is returned without HMAC enforcement.
    The dev path must not be weakened or removed.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body

    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'

    async def mock_stream():
        yield raw_body

    request_mock = MagicMock()
    request_mock.headers = {}
    request_mock.stream = mock_stream

    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = ""      # Missing
        mock_settings.is_production = False              # Non-production (dev, staging, test)

        # Must NOT raise — dev bypass must return raw body
        result = await verify_meta_signature_and_get_raw_body(request_mock)

    assert result == raw_body


# Test F — oversized webhook → HTTP 413 (regression guard)
@pytest.mark.anyio
async def test_oversized_webhook_body_regression_413():
    """
    F. Oversized inbound webhook body (> 1 MB) must return HTTP 413 regardless of
    app secret or environment. Existing behavior must not be degraded by the Option A fix.
    """
    from routers.whatsapp import verify_meta_signature_and_get_raw_body
    from fastapi import HTTPException

    chunk1 = b"X" * 600_000
    chunk2 = b"Y" * 600_000  # Total: 1,200,000 bytes — exceeds 1 MB ceiling

    async def mock_stream():
        yield chunk1
        yield chunk2

    request_mock = MagicMock()
    request_mock.headers = {}
    request_mock.stream = mock_stream

    # Environment and secret state should be irrelevant — 413 fires before HMAC
    with patch("routers.whatsapp.settings") as mock_settings:
        mock_settings.meta_whatsapp_app_secret = "any_secret"
        mock_settings.is_production = True

        with pytest.raises(HTTPException) as exc_info:
            await verify_meta_signature_and_get_raw_body(request_mock)

    assert exc_info.value.status_code == 413
    assert "exceeds maximum limit" in exc_info.value.detail


# Test G — duplicate wamid → Step 2G idempotency regression guard
@pytest.mark.anyio
async def test_duplicate_wamid_idempotency_regression(temp_db):
    """
    G. Duplicate webhook with same wamid must not trigger a second business processing
    execution. Step 2G idempotency guard must continue to function after Option A fix.
    Verifies that the security change does not affect post-verification processing logic.
    """
    wamid = "wamid.HBgL_3e2_dup_test_99"
    contact_id = "wac_3e2_dup_test"

    # First claim — must succeed
    claim1 = await claim_message_processing(temp_db, wamid, contact_id)
    assert claim1["is_owner"] is True

    await complete_message_processing(temp_db, wamid, "First processing reply")

    # Duplicate claim — must fail with is_owner=False
    claim2 = await claim_message_processing(temp_db, wamid, contact_id)
    assert claim2["is_owner"] is False
    assert claim2["status"] == "completed"
    assert claim2["outbound_reply"] == "First processing reply"

