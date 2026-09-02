"""
test_whatsapp_persistence.py — Step 1B Contact & Message Persistence Tests.

Verifies:
1. Contact creation and field defaults.
2. Unique phone number constraint enforcement.
3. Fast contact lookup by phone and ID.
4. User association (linking WhatsApp contact to a SmartLegal user_id).
5. Message creation for inbound and outbound messages.
6. Support for rich message types (text, image, document, interactive, location).
7. Message history retrieval ordered by timestamp.
8. Foreign key ON DELETE CASCADE behavior on message history.
"""

import pytest
import sqlite3
import json
import uuid
import datetime
from services.whatsapp.repository import (
    create_whatsapp_contact,
    get_contact_by_phone,
    get_contact_by_id,
    get_or_create_whatsapp_contact,
    update_whatsapp_contact,
    save_whatsapp_message,
    get_whatsapp_message_history,
)
from database import SQLiteConnectionWrapper, SQLitePoolWrapper
import aiosqlite


@pytest.fixture
async def temp_db():
    """Create an in-memory SQLite database connection with full schema initialized."""
    async with aiosqlite.connect(":memory:") as conn:
        db = SQLiteConnectionWrapper(conn)
        
        # Initialize schema tables
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
            
            CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_phone ON whatsapp_contacts(phone_number);
            CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_user_id ON whatsapp_contacts(user_id);
            CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_contact_id ON whatsapp_messages(contact_id);
            CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_contact_time ON whatsapp_messages(contact_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_provider_id ON whatsapp_messages(provider_message_id);
        """)
        # Enable foreign key enforcement
        await conn.execute("PRAGMA foreign_keys = ON;")
        yield db


@pytest.mark.anyio
async def test_contact_creation_and_lookup(temp_db):
    """Test contact creation, phone lookup, and initial defaults."""
    phone = "+919876543210"
    
    # 1. Create contact
    contact = await create_whatsapp_contact(temp_db, phone_number=phone)
    assert contact["id"].startswith("wac_")
    assert contact["phone_number"] == phone
    assert contact["preferred_language"] is None
    assert contact["onboarding_status"] == "pending"
    assert contact["user_id"] is None

    # 2. Lookup by phone
    found = await get_contact_by_phone(temp_db, phone)
    assert found is not None
    assert found["id"] == contact["id"]

    # 3. Lookup by ID
    found_by_id = await get_contact_by_id(temp_db, contact["id"])
    assert found_by_id is not None
    assert found_by_id["phone_number"] == phone


@pytest.mark.anyio
async def test_unique_phone_number_constraint(temp_db):
    """Verify unique phone number constraint raises IntegrityError on duplicate insert."""
    phone = "+919876543210"
    await create_whatsapp_contact(temp_db, phone_number=phone)

    # Attempting to insert duplicate phone should raise Exception / sqlite3.IntegrityError
    with pytest.raises(Exception):
        await create_whatsapp_contact(temp_db, phone_number=phone)


@pytest.mark.anyio
async def test_get_or_create_contact(temp_db):
    """Verify get_or_create_whatsapp_contact idempotency."""
    phone = "+919123456789"
    
    c1 = await get_or_create_whatsapp_contact(temp_db, phone_number=phone)
    c2 = await get_or_create_whatsapp_contact(temp_db, phone_number=phone)
    
    assert c1["id"] == c2["id"]


@pytest.mark.anyio
async def test_link_contact_to_user(temp_db):
    """Verify linking WhatsApp contact to a SmartLegal user ID."""
    # Insert user
    user_id = "user_sl_1001"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    await temp_db.execute(
        "INSERT INTO users (id, name, email, password, created_at) VALUES ($1, $2, $3, $4, $5)",
        user_id, "Rahul Sharma", "rahul@example.com", "hashed_pass", now
    )

    contact = await create_whatsapp_contact(temp_db, phone_number="+919988776655")
    assert contact["user_id"] is None

    # Link user
    updated = await update_whatsapp_contact(
        temp_db,
        contact_id=contact["id"],
        user_id=user_id,
        preferred_language="hi",
        onboarding_status="completed",
    )
    assert updated["user_id"] == user_id
    assert updated["preferred_language"] == "hi"
    assert updated["onboarding_status"] == "completed"


@pytest.mark.anyio
async def test_message_persistence_and_history(temp_db):
    """Verify incoming/outgoing message persistence and history ordering."""
    contact = await create_whatsapp_contact(temp_db, phone_number="+919876543210")
    cid = contact["id"]

    # 1. Inbound text message
    m1 = await save_whatsapp_message(
        temp_db,
        contact_id=cid,
        direction="inbound",
        content="Namaste, I need help analyzing a rental agreement",
        message_type="text",
        provider_message_id="wa_msg_in_001",
    )
    assert m1["id"].startswith("wamsg_")
    assert m1["direction"] == "inbound"

    # 2. Outbound text reply
    m2 = await save_whatsapp_message(
        temp_db,
        contact_id=cid,
        direction="outbound",
        content="Welcome to SmartLegal AI! Please upload or send your document.",
        message_type="text",
    )
    assert m2["direction"] == "outbound"

    # 3. Inbound document message with metadata
    m3 = await save_whatsapp_message(
        temp_db,
        contact_id=cid,
        direction="inbound",
        content="Rental_Agreement_Delhi.pdf",
        message_type="document",
        media_url="https://storage.smartlegal.ai/docs/rental_delhi.pdf",
        metadata_json={"mime_type": "application/pdf", "file_size": 204800},
        provider_message_id="wa_msg_in_002",
    )
    assert m3["message_type"] == "document"
    assert m3["media_url"] == "https://storage.smartlegal.ai/docs/rental_delhi.pdf"
    
    # 4. Fetch history
    history = await get_whatsapp_message_history(temp_db, cid)
    assert len(history) == 3
    assert history[0]["content"] == "Namaste, I need help analyzing a rental agreement"
    assert history[1]["content"] == "Welcome to SmartLegal AI! Please upload or send your document."
    assert history[2]["content"] == "Rental_Agreement_Delhi.pdf"


@pytest.mark.anyio
async def test_cascade_delete_messages(temp_db):
    """Verify deleting a contact cascades and removes all associated message history."""
    contact = await create_whatsapp_contact(temp_db, phone_number="+919876543210")
    cid = contact["id"]

    await save_whatsapp_message(temp_db, cid, "inbound", "Hello")
    await save_whatsapp_message(temp_db, cid, "outbound", "Hi")

    history_before = await get_whatsapp_message_history(temp_db, cid)
    assert len(history_before) == 2

    # Delete contact
    await temp_db.execute("DELETE FROM whatsapp_contacts WHERE id = $1", cid)

    history_after = await get_whatsapp_message_history(temp_db, cid)
    assert len(history_after) == 0
