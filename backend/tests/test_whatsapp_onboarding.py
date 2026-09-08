"""
test_whatsapp_onboarding.py — Step 1C Language Selection & Onboarding Flow Tests.

Verifies:
1. New user receives Welcome & Language Selection prompt.
2. Normal menu and workflows are blocked before language selection.
3. Language selection validation for Marathi (1 / marathi / मराठी), Hindi (2 / hindi / हिंदी), English (3 / english).
4. Language selection persistence in whatsapp_contacts DB table.
5. Returning user continues in saved language without auto-repeating main menu.
6. Main menu is delivered immediately after onboarding or on explicit 'menu'/'help' command.
7. Invalid language choices are safely re-prompted.
8. Multilingual language reset commands ("change language", "भाषा बदलें", "भाषा बदला") re-trigger onboarding.
"""

import pytest
from database import SQLiteConnectionWrapper
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.repository import get_contact_by_phone
from services.whatsapp.language import LanguageCode
import aiosqlite


@pytest.fixture
async def temp_db():
    """Create an in-memory SQLite database connection initialized with schema."""
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
async def test_new_user_receives_language_selection(temp_db):
    """Verify first-time user receives Welcome & Language Selection prompt."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543001"
    payload = {"from_phone": phone, "message_text": "Hi"}

    res = await orchestrator.process_inbound_message(payload, db=temp_db)
    assert res.status == "ok"
    assert "Select your language" in res.reply
    assert "Marathi" in res.reply
    assert "Hindi" in res.reply
    assert "English" in res.reply

    contact = await get_contact_by_phone(temp_db, phone)
    assert contact is not None
    assert contact["onboarding_status"] == "pending"
    assert contact["preferred_language"] is None


@pytest.mark.anyio
async def test_normal_menu_blocked_before_language_selection(temp_db):
    """Verify normal menu and questions are blocked before completing language selection."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543002"

    # Send arbitrary question without selecting language
    payload = {"from_phone": phone, "message_text": "Analyze my contract"}
    res = await orchestrator.process_inbound_message(payload, db=temp_db)

    # Should reply with Invalid / Re-prompt language selection
    assert "Invalid selection" in res.reply or "Select your language" in res.reply
    
    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["onboarding_status"] == "pending"


@pytest.mark.anyio
async def test_marathi_language_selection(temp_db):
    """Verify selecting Marathi ('1' or 'मराठी') completes onboarding and delivers Marathi menu."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543003"

    # 1. Initial greeting
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "Hi"}, db=temp_db)

    # 2. Select Marathi by '1'
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)
    assert "भाषा मराठी सेट केली" in res.reply
    assert "कायदेशीर प्रश्न विचारा" in res.reply  # Marathi main menu option

    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.MARATHI
    assert contact["onboarding_status"] == "completed"


@pytest.mark.anyio
async def test_hindi_language_selection(temp_db):
    """Verify selecting Hindi ('2' or 'हिंदी') completes onboarding and delivers Hindi menu."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543004"

    # Select Hindi by native script 'हिंदी'
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "हिंदी"}, db=temp_db)
    assert "भाषा हिंदी पर सेट की गई" in res.reply
    assert "कानूनी प्रश्न पूछें" in res.reply  # Hindi main menu option

    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.HINDI
    assert contact["onboarding_status"] == "completed"


@pytest.mark.anyio
async def test_english_language_selection(temp_db):
    """Verify selecting English ('3' or 'english') completes onboarding and delivers English menu."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543005"

    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "english"}, db=temp_db)
    assert "Language set to English" in res.reply
    assert "Ask a legal question" in res.reply  # English main menu option

    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["preferred_language"] == LanguageCode.ENGLISH
    assert contact["onboarding_status"] == "completed"


@pytest.mark.anyio
async def test_returning_user_continues_without_auto_main_menu(temp_db):
    """
    Verify returning user continues conversation in saved language without auto-repeating main menu on every message.
    Main menu is only served when explicitly requested.
    """
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543006"

    # 1. Onboard in Marathi
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "मराठी"}, db=temp_db)

    # 2. Returning user sends specific query
    msg_res = await orchestrator.process_inbound_message(
        {"from_phone": phone, "message_text": "माझी legal notice समजावून सांगा"},
        db=temp_db,
    )
    assert "SmartLegal AI — Main Menu" not in msg_res.reply
    assert "notice" in msg_res.reply.lower() or "नोटीस" in msg_res.reply or "संवाद" in msg_res.reply

    # 3. Returning user explicitly asks for menu
    menu_res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "menu"}, db=temp_db)
    assert "कायदेशीर प्रश्न विचारा" in menu_res.reply


@pytest.mark.anyio
async def test_multilingual_language_reset_command(temp_db):
    """Verify language change commands in English, Hindi, and Marathi reset onboarding."""
    orchestrator = WhatsAppOrchestrator()
    phone = "+919876543007"

    # Onboard in English
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # Change language using Marathi command 'भाषा बदला'
    reset_res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "भाषा बदला"}, db=temp_db)
    assert "Select your language" in reset_res.reply

    contact = await get_contact_by_phone(temp_db, phone)
    assert contact["onboarding_status"] == "pending"

    # Now select Hindi
    hi_res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "2"}, db=temp_db)
    assert "भाषा हिंदी पर सेट की गई" in hi_res.reply
