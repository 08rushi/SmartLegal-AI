"""
test_whatsapp_foundation.py — Step 1D Development Simulator & Foundation Verification Suite.

Verifies end-to-end foundation flows across Marathi, Hindi, and English,
simulator HTTP endpoint execution, database persistence, returning contact state,
and error validation.
"""

import pytest
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.repository import get_contact_by_phone, get_whatsapp_message_history
from services.whatsapp.language import LanguageCode
from main import app
import aiosqlite


@pytest.fixture
async def temp_db():
    """Create an in-memory SQLite database connection with schema."""
    async with aiosqlite.connect(":memory:") as conn:
        db = SQLiteConnectionWrapper(conn)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                password      TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                token_version INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS whatsapp_contacts (
                id                 TEXT PRIMARY KEY,
                phone_number       TEXT UNIQUE NOT NULL,
                user_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
                preferred_language TEXT DEFAULT NULL,
                onboarding_status  TEXT NOT NULL DEFAULT 'pending',
                created_at         TEXT NOT NULL,
                updated_at         TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id                  TEXT PRIMARY KEY,
                contact_id          TEXT NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
                direction           TEXT NOT NULL,
                message_type        TEXT NOT NULL DEFAULT 'text',
                content             TEXT NOT NULL,
                media_url           TEXT DEFAULT NULL,
                metadata_json       TEXT DEFAULT '{}',
                provider_message_id TEXT DEFAULT NULL,
                created_at          TEXT NOT NULL
            );
        """)
        await conn.execute("PRAGMA foreign_keys = ON;")
        yield db


@pytest.mark.anyio
async def test_full_marathi_flow(temp_db):
    """
    Verify complete Marathi flow:
    New Phone -> Welcome Prompt -> Select Marathi -> Confirmation + Marathi Menu -> Subsequent Msg -> Marathi Response -> Explicit Menu
    """
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876544001"

    # 1. New Phone -> Initial Message
    r1 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "Hi"}, db=temp_db)
    assert "Welcome to SmartLegal AI" in r1.reply
    assert "Select your language" in r1.reply

    # 2. Select Marathi ('1')
    r2 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)
    assert "भाषा मराठी सेट केली" in r2.reply
    assert "कायदेशीर प्रश्न विचारा" in r2.reply

    # 3. Subsequent Message -> Marathi Response (no auto menu repeat)
    r3 = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "माझी legal notice समजावून सांगा"}, db=temp_db
    )
    assert "SmartLegal AI — Main Menu" not in r3.reply
    assert "notice" in r3.reply.lower() or "नोटीस" in r3.reply or "संवाद" in r3.reply

    # 4. Explicit Menu Request
    r4 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "menu"}, db=temp_db)
    assert "कायदेशीर प्रश्न विचारा" in r4.reply

    # 5. DB Persistence Verification
    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.MARATHI
    assert contact["onboarding_status"] == "completed"

    history = await get_whatsapp_message_history(temp_db, contact["id"])
    assert len(history) == 8  # 4 inbound + 4 outbound messages


@pytest.mark.anyio
async def test_full_hindi_flow(temp_db):
    """
    Verify complete Hindi flow:
    New Phone -> Welcome Prompt -> Select Hindi -> Confirmation + Hindi Menu -> Subsequent Msg -> Hindi Response -> Explicit Menu
    """
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876544002"

    # 1. New Phone -> Initial Message
    r1 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "Namaste"}, db=temp_db)
    assert "Select your language" in r1.reply

    # 2. Select Hindi ('हिंदी')
    r2 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "हिंदी"}, db=temp_db)
    assert "भाषा हिंदी पर सेट की गई" in r2.reply
    assert "कानूनी प्रश्न पूछें" in r2.reply

    # 3. Subsequent Message -> Hindi Response
    r3 = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "मुझे किराए का एग्रीमेंट समझना है"}, db=temp_db
    )
    assert "मुख्य मेनू" not in r3.reply
    assert "दस्तावेज़" in r3.reply or "एग्रीमेंट" in r3.reply or "बातचीत" in r3.reply

    # 4. Explicit Menu Request in Hindi ('मदद')
    r4 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "मदद"}, db=temp_db)
    assert "कानूनी प्रश्न पूछें" in r4.reply

    # DB Check
    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.HINDI
    assert contact["onboarding_status"] == "completed"


@pytest.mark.anyio
async def test_full_english_flow(temp_db):
    """
    Verify complete English flow:
    New Phone -> Welcome Prompt -> Select English -> Confirmation + English Menu -> Subsequent Msg -> English Response
    """
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876544003"

    # 1. New Phone -> Initial Message
    r1 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "Hello"}, db=temp_db)
    assert "Select your language" in r1.reply

    # 2. Select English ('english')
    r2 = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "english"}, db=temp_db)
    assert "Language set to English" in r2.reply
    assert "Ask a legal question" in r2.reply

    # 3. Subsequent Message -> English Response
    r3 = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "Draft an NDA for my startup"}, db=temp_db
    )
    assert "Main Menu" not in r3.reply
    assert "draft" in r3.reply.lower() or "document" in r3.reply.lower() or "conversation" in r3.reply.lower()

    # DB Check
    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.ENGLISH
    assert contact["onboarding_status"] == "completed"


def test_simulator_http_endpoint(client):
    """
    Verify simulator HTTP endpoint POST /api/v1/whatsapp/simulate-inbound
    executes through the exact same orchestrator & adapter pipeline.
    """
    import uuid
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # 1. Initial message via HTTP API
    resp1 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": phone, "message_text": "Hi"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "ok"
    assert "Select your language" in data1["reply"]

    # 2. Select English via HTTP API
    resp2 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": phone, "message_text": "3"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "Language set to English" in data2["reply"]
    assert "Ask a legal question" in data2["reply"]

    # 3. Ask question via HTTP API
    resp3 = client.post(
        "/api/v1/whatsapp/simulate-inbound",
        json={"from_phone": phone, "message_text": "What are my rights under consumer law?"},
    )
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["status"] == "ok"
    assert len(data3["reply"]) > 10
    assert "Main Menu" not in data3["reply"]


def test_simulator_validation_errors(client):
    """Verify HTTP API error handling for invalid/missing parameters."""
    # Missing phone
    resp1 = client.post("/api/v1/whatsapp/simulate-inbound", json={"message_text": "Hello"})
    assert resp1.status_code == 422

    # Blank phone
    resp2 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": "   ", "message_text": "Hello"})
    assert resp2.status_code == 400

    # Blank text
    resp3 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": "+919876543210", "message_text": "   "})
    assert resp3.status_code == 400
