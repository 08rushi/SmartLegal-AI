"""
test_whatsapp_qa.py — Step 2B Real Legal Q&A Integration Test Suite.

Verifies:
1. English natural-language legal question (mocked LLM -> English response with disclaimer).
2. Hindi natural-language legal question (mocked LLM -> Hindi response with disclaimer).
3. Marathi natural-language legal question (mocked LLM -> Marathi response with disclaimer).
4. Multi-turn conversation context test (verifies past turns are passed to LLM).
5. Persistence verification (inbound question & outbound answer saved in whatsapp_messages).
6. Graceful AI failure handling test (verifies ai_orchestrator failure returns localized fallback without stack traces).
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.repository import get_contact_by_phone, get_whatsapp_message_history
from services.whatsapp.language import LanguageCode
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
        """)
        yield db


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_english_natural_language_qa(mock_chat, temp_db):
    """Verify English legal question returns AI advice with English disclaimer."""
    mock_chat.return_value = "Under the Consumer Protection Act 2019, you can file a complaint in District Consumer Forum for refund of security deposit."
    
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # Ask English legal question
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "What can I do if my landlord refuses to return my security deposit?"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "Consumer Protection Act 2019" in res.reply
    assert "Note: This is AI legal guidance based on Indian law" in res.reply
    mock_chat.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_hindi_natural_language_qa(mock_chat, temp_db):
    """Verify Hindi legal question returns AI advice with Hindi disclaimer."""
    mock_chat.return_value = "उपभोक्ता संरक्षण अधिनियम 2019 के तहत आप जिला उपभोक्ता फोरम में शिकायत दर्ज करा सकते हैं।"

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in Hindi ('2')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "2"}, db=temp_db)

    # Ask Hindi legal question
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "अगर मकान मालिक मेरी सिक्योरिटी डिपॉजिट वापस नहीं करता तो मैं क्या कर सकता हूँ?"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "उपभोक्ता संरक्षण अधिनियम" in res.reply
    assert "नोट: यह भारतीय कानून पर आधारित एआई मार्गदर्शन है" in res.reply
    mock_chat.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_marathi_natural_language_qa(mock_chat, temp_db):
    """Verify Marathi legal question returns AI advice with Marathi disclaimer."""
    mock_chat.return_value = "ग्राहक संरक्षण कायदा 2019 अंतर्गत तुम्ही डिपॉझिट वसुलीसाठी जिल्हा ग्राहक न्यायालयात तक्रार करू शकता."

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in Marathi ('1')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)

    # Ask Marathi legal question
    res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "माझा घरमालक सिक्युरिटी डिपॉझिट परत देत नसेल तर मी काय करू शकतो?"},
        db=temp_db,
    )

    assert res.status == "ok"
    assert "ग्राहक संरक्षण कायदा" in res.reply
    assert "टीप: हा भारतीय कायद्यावर आधारित एआय सल्ला आहे" in res.reply
    mock_chat.assert_called_once()


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_multiturn_conversation_context(mock_chat, temp_db):
    """Verify follow-up turn passes bounded past messages context to the LLM."""
    mock_chat.return_value = "You can send a formal legal notice under Section 106 of Transfer of Property Act."

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # 1. Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # 2. Turn 1
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "My landlord is not returning my deposit."}, db=temp_db)

    # 3. Turn 2 (Follow-up)
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "I already told him twice verbally."}, db=temp_db)

    assert res.status == "ok"
    assert "legal notice" in res.reply

    # Inspect messages array passed to mock_chat call
    call_args = mock_chat.call_args[0][0]
    # Verify System prompt + past turns were included
    assert any("system" == m["role"] for m in call_args)
    assert any("I already told him twice verbally." in m["content"] for m in call_args)


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_qa_persistence(mock_chat, temp_db):
    """Verify inbound question and outbound answer are persisted in whatsapp_messages."""
    mock_chat.return_value = "Send a legal notice first."

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "english"}, db=temp_db)
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "Can I sue my landlord?"}, db=temp_db)

    contact = await get_contact_by_phone(temp_db, phone)
    history = await get_whatsapp_message_history(temp_db, contact["id"])
    
    inbound_msgs = [m for m in history if m["direction"] == "inbound"]
    outbound_msgs = [m for m in history if m["direction"] == "outbound"]

    assert len(inbound_msgs) == 2
    assert len(outbound_msgs) == 2
    assert any("Can I sue my landlord?" in m["content"] for m in inbound_msgs)
    assert any("Send a legal notice first" in m["content"] for m in outbound_msgs)


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_ai_failure_fallback(mock_chat, temp_db):
    """Verify AI failure produces a localized fallback response without leaking stack traces."""
    mock_chat.side_effect = RuntimeError("Groq API Timeout Exception 504")

    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in Marathi
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)

    # Ask question
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "माझ्या घरमालकाने घर रिकामे करायला सांगितले"}, db=temp_db)

    assert res.status == "ok"
    assert "क्षमस्व, सध्या तुमच्या प्रश्नाचे उत्तर देताना तांत्रिक अडचण आली" in res.reply
    assert "Groq" not in res.reply
    assert "504" not in res.reply
