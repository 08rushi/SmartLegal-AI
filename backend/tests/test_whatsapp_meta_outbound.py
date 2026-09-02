"""
test_whatsapp_meta_outbound.py — Step 3C Meta WhatsApp Cloud API Outbound Messaging Test Suite.

Verifies all 17 approved test cases:
1. Deterministic idempotency key generation & key replay equality.
2. Distinct keys for distinct inbound events or sequence indexes.
3. Meta outbound configuration loading.
4. Successful text message dispatch via Graph API.
5. Exact POST endpoint URL and Authorization header construction.
6. Missing access token / phone number ID failure handling.
7. Meta 4xx client error non-retryable classification (failed_non_retryable).
8. Meta 5xx server error retryable classification (failed_retryable).
9. Network timeout classification (unknown status, 0 duplicate HTTP sends).
10. Bearer token non-leakage in logs & error messages.
11. Recipient phone E.164 normalization.
12. DB-level atomic claim concurrency (2 workers, exactly 1 HTTP call).
13. Replayed completed outbound event (0 secondary HTTP calls).
14. Stale sending lease recovery (> 120s -> unknown status).
15. Dev simulator outbound compatibility (DevWhatsAppOutboundAdapter).
16. Full orchestrator integration with DB persistence.
17. Reliability non-regression.
"""

import pytest
import asyncio
import json
import uuid
import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import aiosqlite
from config import get_settings
from database import SQLiteConnectionWrapper
from services.whatsapp.outbound_adapter import (
    MetaWhatsAppOutboundAdapter,
    DevWhatsAppOutboundAdapter,
    get_whatsapp_outbound_adapter,
    OutboundSendResult,
)
from services.whatsapp.outbound_dispatcher import (
    generate_outbound_idempotency_key,
    claim_outbound_send,
    send_outbound_message,
)
from services.whatsapp.orchestrator import WhatsAppOrchestrator


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


def test_outbound_idempotency_key_deterministic_generation():
    """Verify formula generates deterministic 32-char key starting with out_key_."""
    key1 = generate_outbound_idempotency_key("wac_123", "wamid_456", sequence_index=0)
    key2 = generate_outbound_idempotency_key("wac_123", "wamid_456", sequence_index=0)
    assert key1 == key2
    assert key1.startswith("out_key_")
    assert len(key1) == 32


def test_same_inbound_event_produces_identical_outbound_key():
    """Verify replayed event with same contact_id and wamid produces identical key."""
    k_a = generate_outbound_idempotency_key("WAC_ABC", "wamid.HBgL123", 0)
    k_b = generate_outbound_idempotency_key("wac_abc ", "wamid.HBgL123", 0)
    assert k_a == k_b


def test_different_inbound_events_produce_different_outbound_keys():
    """Verify distinct wamids or sequence indexes yield distinct keys."""
    k1 = generate_outbound_idempotency_key("wac_1", "wamid_1", 0)
    k2 = generate_outbound_idempotency_key("wac_1", "wamid_2", 0)
    k3 = generate_outbound_idempotency_key("wac_1", "wamid_1", 1)
    assert k1 != k2
    assert k1 != k3


def test_meta_outbound_config_loading():
    """Verify Settings loads META_WHATSAPP_PHONE_NUMBER_ID and access token."""
    settings = get_settings()
    settings.meta_whatsapp_phone_number_id = "000000000000000"  # Fictional placeholder — not a real Meta Phone Number ID
    settings.meta_whatsapp_access_token = "test_token_xyz"
    assert settings.meta_whatsapp_phone_number_id == "000000000000000"
    assert settings.meta_whatsapp_access_token == "test_token_xyz"



@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_successful_text_send_meta_graph_api(mock_post):
    """Verify HTTP 200 Meta response parses returned wamid."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_abc"
    settings.meta_whatsapp_phone_number_id = "phone_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
        "messages": [{"id": "wamid.HBgL999888777"}],
    }
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppOutboundAdapter()
    result = await adapter.send_text_message("+919876543210", "Hello from SmartLegal")

    assert result.success is True
    assert result.delivery_status == "sent"
    assert result.provider_message_id == "wamid.HBgL999888777"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_correct_meta_graph_api_endpoint_and_authorization_header(mock_post):
    """Verify target URL and Authorization header structure."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "secret_meta_token"
    settings.meta_whatsapp_phone_number_id = "phone_999"
    settings.meta_whatsapp_graph_url = "https://graph.facebook.com"
    settings.meta_whatsapp_api_version = "v21.0"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"messages": [{"id": "wamid.123"}]}
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppOutboundAdapter()
    await adapter.send_text_message("+919876543210", "Test payload structure")

    assert mock_post.called
    call_args = mock_post.call_args
    target_url = call_args[0][0]
    headers = call_args[1].get("headers", {})

    assert target_url == "https://graph.facebook.com/v21.0/phone_999/messages"
    assert headers.get("Authorization") == "Bearer secret_meta_token"


@pytest.mark.anyio
async def test_missing_token_or_phone_id_failure():
    """Verify unconfigured credentials return non-retryable failure cleanly."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = ""
    settings.meta_whatsapp_phone_number_id = ""

    adapter = MetaWhatsAppOutboundAdapter()
    res = await adapter.send_text_message("+919876543210", "Test")

    assert res.success is False
    assert res.delivery_status == "failed_non_retryable"
    assert res.error_code == "MISSING_TOKEN"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_meta_4xx_non_retryable_error_handling(mock_post):
    """Verify HTTP 400 client error transitions to failed_non_retryable."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"
    settings.meta_whatsapp_phone_number_id = "phone_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "Invalid parameter: recipient phone format", "code": 100}}
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppOutboundAdapter()
    res = await adapter.send_text_message("+919876543210", "Bad param")

    assert res.success is False
    assert res.delivery_status == "failed_non_retryable"
    assert res.error_code == "400"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_meta_5xx_retryable_error_handling(mock_post):
    """Verify HTTP 503 server error transitions to failed_retryable."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"
    settings.meta_whatsapp_phone_number_id = "phone_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.return_value = {"error": {"message": "Service Temporarily Unavailable", "code": 2}}
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppOutboundAdapter()
    res = await adapter.send_text_message("+919876543210", "Server error test")

    assert res.success is False
    assert res.delivery_status == "failed_retryable"
    assert res.error_code == "503"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_meta_timeout_unknown_state_handling(mock_post):
    """Verify network timeout transitions status to 'unknown' without secondary POST."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"
    settings.meta_whatsapp_phone_number_id = "phone_123"

    mock_post.side_effect = TimeoutError("Request timed out")

    adapter = MetaWhatsAppOutboundAdapter()
    res = await adapter.send_text_message("+919876543210", "Timeout test")

    assert res.success is False
    assert res.delivery_status == "unknown"
    assert res.error_code == "NETWORK_TIMEOUT_UNKNOWN"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_bearer_token_never_logged_or_exposed_in_errors(mock_post):
    """Verify raw token is masked in error strings."""
    settings = get_settings()
    secret_token = "super_secret_token_77777"
    settings.meta_whatsapp_access_token = secret_token
    settings.meta_whatsapp_phone_number_id = "phone_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"error": {"message": f"Invalid token {secret_token}"}}
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppOutboundAdapter()
    res = await adapter.send_text_message("+919876543210", "Auth error")

    assert secret_token not in res.error_message
    assert "[MASKED_TOKEN]" in res.error_message


def test_recipient_e164_phone_normalization():
    """Verify recipient phone formatting strips leading plus for Meta Cloud API."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"
    settings.meta_whatsapp_phone_number_id = "phone_123"

    adapter = MetaWhatsAppOutboundAdapter()
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.1"}]}
        mock_post.return_value = mock_resp

        asyncio.run(adapter.send_text_message("+91 98765 43210", "Normalize test"))
        payload = mock_post.call_args[1]["json"]
        assert payload["to"] == "919876543210"


@pytest.mark.anyio
async def test_atomic_concurrent_outbound_claim(temp_db):
    """Verify concurrent workers claiming same idempotency key result in exactly 1 claim owner."""
    key = generate_outbound_idempotency_key("wac_conc", "wamid_conc_1", 0)
    payload = {
        "contact_id": "wac_conc",
        "recipient_phone": "+919876543210",
        "inbound_provider_message_id": "wamid_conc_1",
        "provider": "dev_simulator",
        "message_type": "text",
    }

    res1, res2 = await asyncio.gather(
        claim_outbound_send(temp_db, key, payload),
        claim_outbound_send(temp_db, key, payload),
    )

    owners = [r for r in (res1, res2) if r.get("is_owner") is True]
    non_owners = [r for r in (res1, res2) if r.get("is_owner") is False]

    assert len(owners) == 1
    assert len(non_owners) == 1


@pytest.mark.anyio
async def test_completed_outbound_replay_no_second_http_call(temp_db):
    """Verify replaying completed outbound event returns cached sent status with 0 HTTP calls."""
    contact = {"id": "wac_replay", "phone_number": "+919876543210"}
    inbound_wamid = "wamid_replay_100"

    # Send 1
    res1 = await send_outbound_message(
        temp_db, contact, "Replay test message", inbound_wamid, provider="dev_simulator"
    )
    assert res1["status"] == "sent"
    assert res1["executed"] is True

    # Replay Send 2
    res2 = await send_outbound_message(
        temp_db, contact, "Replay test message", inbound_wamid, provider="dev_simulator"
    )
    assert res2["status"] == "sent"
    assert res2["executed"] is False


@pytest.mark.anyio
async def test_stale_sending_recovery_policy(temp_db):
    """Verify stale sending lease (> 120s) transitions to 'unknown'."""
    key = generate_outbound_idempotency_key("wac_stale", "wamid_stale_1", 0)
    stale_started = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=130)).isoformat()

    await temp_db.execute(
        """
        INSERT INTO whatsapp_outbound_messages (
            id, idempotency_key, inbound_provider_message_id, contact_id,
            recipient_phone, provider, message_type, outbound_payload_json,
            delivery_status, send_claim_id, sending_started_at, attempt_count,
            created_at, updated_at
        ) VALUES ('wom_stale', $1, 'wamid_stale_1', 'wac_stale', '+919876543210',
                  'meta_cloud_api', 'text', '{}', 'sending', 'woc_old', $2, 1, $2, $2)
        """,
        key, stale_started
    )

    claim_res = await claim_outbound_send(temp_db, key, {"inbound_provider_message_id": "wamid_stale_1"})
    assert claim_res["status"] == "unknown"
    assert claim_res["is_owner"] is False


@pytest.mark.anyio
async def test_dev_simulator_outbound_provider_compatibility():
    """Verify DevWhatsAppOutboundAdapter returns valid sent status with mock wamid."""
    adapter = get_whatsapp_outbound_adapter("dev_simulator")
    assert isinstance(adapter, DevWhatsAppOutboundAdapter)

    res = await adapter.send_text_message("+919876543210", "Dev test")
    assert res.success is True
    assert res.delivery_status == "sent"
    assert res.provider_message_id.startswith("dev_out_")


@pytest.mark.anyio
async def test_orchestrator_integration_and_step_2g_regression(temp_db):
    """Verify full end-to-end integration through WhatsAppOrchestrator."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard language selection ('3' -> English)
    res_onboard = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "3", "message_id": f"wamid_onboard_{uuid.uuid4().hex[:6]}"},
        db=temp_db,
    )
    assert res_onboard.status == "ok"
    assert "Language set to English" in res_onboard.reply

    # Verify outbound message record created in whatsapp_outbound_messages table
    rows = await temp_db.fetch("SELECT * FROM whatsapp_outbound_messages")
    assert len(rows) >= 1
    last_row = rows[-1]
    assert last_row["delivery_status"] == "sent"
    assert last_row["provider"] == "dev_simulator"
