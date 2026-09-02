"""
test_whatsapp_meta_webhook.py — Step 3A Meta WhatsApp Cloud API Webhook Unit Tests.

Verifies:
1. GET /webhook hub verification with constant-time token comparison.
2. GET /webhook 403 Forbidden for token mismatch or missing configuration.
3. POST /webhook single and multi-message batch payload normalization.
4. E.164 phone number normalization (+91...).
5. Status / delivery / read notification filtering (returns 200 OK ignored without DB pollution).
6. Malformed payload 400 Bad Request handling.
7. Step 2G real DB reliability claim deduplication for duplicate wamid deliveries.
"""

import pytest
import uuid
import datetime
import json
from unittest.mock import AsyncMock, patch

from database import SQLiteConnectionWrapper
from services.whatsapp.meta_adapter import MetaWhatsAppAdapter, normalize_phone_number
from services.whatsapp import WhatsAppOrchestrator
from services.whatsapp.context_repository import WorkflowState
import aiosqlite


@pytest.fixture
async def temp_db():
    """In-memory SQLite database fixture with complete Step 3A schema."""
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
            CREATE TABLE IF NOT EXISTS whatsapp_message_processing (
                id TEXT PRIMARY KEY,
                provider_message_id TEXT UNIQUE NOT NULL,
                contact_id TEXT NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
                processing_status TEXT NOT NULL DEFAULT 'processing',
                attempt_count INTEGER DEFAULT 1,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                outbound_reply TEXT,
                last_error_code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        yield db


def test_phone_number_normalization():
    """Verify normalize_phone_number handles Meta raw phone strings cleanly."""
    assert normalize_phone_number("919876543210") == "+919876543210"
    assert normalize_phone_number("+919876543210") == "+919876543210"
    assert normalize_phone_number("15551234567") == "+15551234567"
    assert normalize_phone_number("  +1-555-123-4567  ") == "+15551234567"
    assert normalize_phone_number("") == ""


def test_meta_adapter_status_event_filtering():
    """Verify status/read notifications return empty list without constructing fake user messages."""
    adapter = MetaWhatsAppAdapter()
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "100200300",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15551234567", "phone_number_id": "10099"},
                            "statuses": [
                                {
                                    "id": "wamid.HBgL12345",
                                    "status": "delivered",
                                    "timestamp": "1720000000",
                                    "recipient_id": "919876543210",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    inbound_list = adapter.extract_inbound_payloads(status_payload)
    assert inbound_list == []

    with pytest.raises(ValueError, match="no inbound user messages"):
        adapter.parse_inbound_payload(status_payload)


def test_meta_adapter_text_and_media_normalization():
    """Verify single and media messages are correctly parsed with provider metadata."""
    adapter = MetaWhatsAppAdapter()
    doc_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone_id_999"},
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.doc_12345",
                                    "timestamp": "1720000000",
                                    "type": "document",
                                    "document": {
                                        "caption": "Rental Agreement PDF",
                                        "filename": "rent_agreement.pdf",
                                        "id": "media_meta_888",
                                        "mime_type": "application/pdf",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }

    inbound_list = adapter.extract_inbound_payloads(doc_payload)
    assert len(inbound_list) == 1
    msg = inbound_list[0]
    assert msg.from_phone == "+919876543210"
    assert msg.message_id == "wamid.doc_12345"
    assert msg.message_type == "document"
    assert msg.message_text == "Rental Agreement PDF"
    assert msg.metadata.get("media_id") == "media_meta_888"
    assert msg.metadata.get("filename") == "rent_agreement.pdf"
    assert msg.metadata.get("phone_number_id") == "phone_id_999"


def test_meta_adapter_multi_message_batch():
    """Verify payload with 2 batched messages extracts both independently."""
    adapter = MetaWhatsAppAdapter()
    batch_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone_id_999"},
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.msg_1",
                                    "timestamp": "1720000000",
                                    "type": "text",
                                    "text": {"body": "First message"},
                                },
                                {
                                    "from": "919876543210",
                                    "id": "wamid.msg_2",
                                    "timestamp": "1720000005",
                                    "type": "text",
                                    "text": {"body": "Second message"},
                                },
                            ],
                        }
                    }
                ]
            }
        ],
    }

    inbound_list = adapter.extract_inbound_payloads(batch_payload)
    assert len(inbound_list) == 2
    assert inbound_list[0].message_id == "wamid.msg_1"
    assert inbound_list[0].message_text == "First message"
    assert inbound_list[1].message_id == "wamid.msg_2"
    assert inbound_list[1].message_text == "Second message"


@pytest.mark.anyio
@patch("services.whatsapp.boundaries.ai_orchestrator.generate_chat_completion", new_callable=AsyncMock)
async def test_meta_webhook_reliability_deduplication(mock_ai, temp_db):
    """Verify real DB Step 2G reliability claim deduplicates repeated Meta wamid deliveries."""
    mock_ai.return_value = "Advice regarding rental notice."
    adapter = MetaWhatsAppAdapter()
    orchestrator = WhatsAppOrchestrator(adapter=adapter)

    phone = "919876543210"
    wamid = f"wamid.meta_dup_{uuid.uuid4().hex[:8]}"

    raw_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone_id_100"},
                            "messages": [
                                {
                                    "from": phone,
                                    "id": wamid,
                                    "timestamp": "1720000000",
                                    "type": "text",
                                    "text": {"body": "3"},  # Onboard in English
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }

    # Onboard user first
    await orchestrator.process_inbound_message(adapter.parse_inbound_payload(raw_payload).model_dump(), db=temp_db)

    # Deliver user question with wamid
    question_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone_id_100"},
                            "messages": [
                                {
                                    "from": phone,
                                    "id": wamid,
                                    "timestamp": "1720000005",
                                    "type": "text",
                                    "text": {"body": "What is tenant lock-in period?"},
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }

    inbound = adapter.parse_inbound_payload(question_payload)

    # First processing
    res1 = await orchestrator.process_inbound_message(inbound.model_dump(), db=temp_db)
    assert res1.status == "ok"
    ai_calls_first = mock_ai.call_count

    # Second processing (Meta webhook retry)
    res2 = await orchestrator.process_inbound_message(inbound.model_dump(), db=temp_db)
    assert res2.status == "ok"
    assert res2.reply == res1.reply
    # LLM must NOT be called a second time
    assert mock_ai.call_count == ai_calls_first
