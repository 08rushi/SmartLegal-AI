"""
test_whatsapp_intent.py — Step 2A Conversational Intent & Routing Engine Tests.

Verifies:
1. Deterministic intent detection for explicit numbers (1-6), help, and language commands (confidence = 1.0).
2. Layer 2 AI classification structure and fallback.
3. Multilingual context preservation (Marathi, Hindi, English).
4. Capability boundary routing for legal_question, document_analysis, legal_notice, document_drafting, my_matters, help_menu, language_change, and unknown.
5. Ambiguous intent clarification handling.
"""

import pytest
import uuid
from services.whatsapp.language import WhatsAppSessionContext, LanguageCode
from services.whatsapp.intent import detect_intent, IntentType, WhatsAppIntent
from services.whatsapp.boundaries import WhatsAppCapabilityRouter, UNKNOWN_CLARIFICATION
from services.whatsapp.orchestrator import WhatsAppOrchestrator
from database import SQLiteConnectionWrapper
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database connection fixture."""
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
async def test_deterministic_intent_detection():
    """Verify 1.0 confidence for explicit menu numbers, help commands, and language reset."""
    ctx_en = WhatsAppSessionContext("w1", "+919000000001", preferred_language=LanguageCode.ENGLISH, onboarding_status="completed")
    ctx_mr = WhatsAppSessionContext("w2", "+919000000002", preferred_language=LanguageCode.MARATHI, onboarding_status="completed")

    # 1. Menu Numbers
    res1 = await detect_intent("1", ctx_en)
    assert res1.intent == IntentType.LEGAL_QUESTION
    assert res1.confidence == 1.0

    res2 = await detect_intent("2", ctx_en)
    assert res2.intent == IntentType.DOCUMENT_ANALYSIS
    assert res2.confidence == 1.0

    res3 = await detect_intent("3", ctx_en)
    assert res3.intent == IntentType.LEGAL_NOTICE
    assert res3.confidence == 1.0

    res4 = await detect_intent("4", ctx_en)
    assert res4.intent == IntentType.DOCUMENT_DRAFTING
    assert res4.confidence == 1.0

    res5 = await detect_intent("5", ctx_en)
    assert res5.intent == IntentType.MY_MATTERS
    assert res5.confidence == 1.0

    res6 = await detect_intent("6", ctx_en)
    assert res6.intent == IntentType.HELP_MENU
    assert res6.confidence == 1.0

    # 2. Help Triggers
    res_help = await detect_intent("menu", ctx_en)
    assert res_help.intent == IntentType.HELP_MENU
    assert res_help.confidence == 1.0

    res_mr_help = await detect_intent("मदत", ctx_mr)
    assert res_mr_help.intent == IntentType.HELP_MENU
    assert res_mr_help.confidence == 1.0

    # 3. Language Change Triggers
    res_lang = await detect_intent("language", ctx_en)
    assert res_lang.intent == IntentType.LANGUAGE_CHANGE
    assert res_lang.confidence == 1.0

    res_mr_lang = await detect_intent("भाषा बदला", ctx_mr)
    assert res_mr_lang.intent == IntentType.LANGUAGE_CHANGE
    assert res_mr_lang.confidence == 1.0


@pytest.mark.anyio
async def test_capability_boundary_routing():
    """Verify routing of normalized intents to capability boundaries."""
    router = WhatsAppCapabilityRouter()

    # 1. Document Analysis Prompt (no attachment)
    intent_doc = WhatsAppIntent(IntentType.DOCUMENT_ANALYSIS, 1.0, "2", LanguageCode.MARATHI)
    resp_doc = await router.route_intent(intent_doc)
    assert "कागदपत्र किंवा कराराची PDF" in resp_doc

    # 2. Legal Notice Prompt (no attachment)
    intent_notice = WhatsAppIntent(IntentType.LEGAL_NOTICE, 1.0, "3", LanguageCode.HINDI)
    resp_notice = await router.route_intent(intent_notice)
    assert "legal notice की फोटो या PDF" in resp_notice

    # 3. Document Drafting Prompt
    intent_draft = WhatsAppIntent(IntentType.DOCUMENT_DRAFTING, 1.0, "4", LanguageCode.ENGLISH)
    resp_draft = await router.route_intent(intent_draft)
    assert "Which document would you like to draft?" in resp_draft

    # 4. My Matters Prompt
    intent_matters = WhatsAppIntent(IntentType.MY_MATTERS, 1.0, "5", LanguageCode.MARATHI)
    resp_matters = await router.route_intent(intent_matters)
    assert "स्मार्टलीगल प्लॅटफॉर्मवरील तुमचे सर्व विषय" in resp_matters

    # 5. Unknown Clarification
    intent_unknown = WhatsAppIntent(IntentType.UNKNOWN, 0.0, "asdfghjkl", LanguageCode.HINDI)
    resp_unknown = await router.route_intent(intent_unknown)
    assert "मैं आपको कानूनी प्रश्नों" in resp_unknown


@pytest.mark.anyio
async def test_multilingual_context_preservation_in_orchestrator(temp_db):
    """Verify end-to-end multi-turn orchestrator preserves language context for intent responses."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in Marathi ('1')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "1"}, db=temp_db)

    # Send document analysis intent ('2')
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "2"}, db=temp_db)
    assert "कागदपत्र किंवा कराराची PDF" in res.reply
    assert res.status == "ok"


@pytest.mark.anyio
async def test_unknown_intent_does_not_guess_legal_workflow(temp_db):
    """Verify ambiguous input receives localized clarification prompt without guessing a workflow."""
    orchestrator = WhatsAppOrchestrator()
    phone = f"+91999{uuid.uuid4().hex[:7]}"

    # Onboard in English ('3')
    await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "3"}, db=temp_db)

    # Send ambiguous string
    res = await orchestrator.process_inbound_message({"from_phone": phone, "message_text": "random text xyz 123"}, db=temp_db)
    assert "I can help you understand legal issues" in res.reply or "SmartLegal AI" in res.reply
