"""
repository.py — Data persistence layer for WhatsApp contacts and message history.

Supports both asyncpg (PostgreSQL pool) and aiosqlite (Local development).
"""

import uuid
import json
import datetime
from typing import Optional, List, Dict, Any


def _get_utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


async def get_contact_by_phone(db, phone_number: str) -> Optional[Dict[str, Any]]:
    """Retrieve WhatsApp contact by unique phone number."""
    row = await db.fetchrow("SELECT * FROM whatsapp_contacts WHERE phone_number = $1", phone_number)
    return dict(row) if row else None


async def get_contact_by_id(db, contact_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve WhatsApp contact by primary key ID."""
    row = await db.fetchrow("SELECT * FROM whatsapp_contacts WHERE id = $1", contact_id)
    return dict(row) if row else None


async def create_whatsapp_contact(
    db,
    phone_number: str,
    user_id: Optional[str] = None,
    preferred_language: Optional[str] = None,
    onboarding_status: str = "pending",
) -> Dict[str, Any]:
    """Create a new WhatsApp contact."""
    contact_id = f"wac_{uuid.uuid4().hex[:12]}"
    now = _get_utc_now()

    await db.execute(
        """
        INSERT INTO whatsapp_contacts (
            id, phone_number, user_id, preferred_language, onboarding_status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        contact_id,
        phone_number,
        user_id,
        preferred_language,
        onboarding_status,
        now,
        now,
    )
    return {
        "id": contact_id,
        "phone_number": phone_number,
        "user_id": user_id,
        "preferred_language": preferred_language,
        "onboarding_status": onboarding_status,
        "created_at": now,
        "updated_at": now,
    }


async def get_or_create_whatsapp_contact(
    db,
    phone_number: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch existing contact by phone number or create a new contact if not present."""
    existing = await get_contact_by_phone(db, phone_number)
    if existing:
        if user_id and not existing.get("user_id"):
            updated = await update_whatsapp_contact(db, existing["id"], user_id=user_id)
            return updated or existing
        return existing

    return await create_whatsapp_contact(db, phone_number, user_id=user_id)


async def update_whatsapp_contact(
    db,
    contact_id: str,
    user_id: Optional[str] = None,
    preferred_language: Optional[str] = None,
    onboarding_status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update contact attributes (user association, preferred language, onboarding status)."""
    current = await get_contact_by_id(db, contact_id)
    if not current:
        return None

    new_user_id = user_id if user_id is not None else current.get("user_id")
    new_lang = preferred_language if preferred_language is not None else current.get("preferred_language")
    new_status = onboarding_status if onboarding_status is not None else current.get("onboarding_status")
    now = _get_utc_now()

    await db.execute(
        """
        UPDATE whatsapp_contacts
        SET user_id = $1, preferred_language = $2, onboarding_status = $3, updated_at = $4
        WHERE id = $5
        """,
        new_user_id,
        new_lang,
        new_status,
        now,
        contact_id,
    )
    return await get_contact_by_id(db, contact_id)


async def update_contact_language(
    db,
    contact_id: str,
    language_code: str,
) -> Optional[Dict[str, Any]]:
    """Save selected language and mark onboarding status as completed."""
    return await update_whatsapp_contact(
        db,
        contact_id,
        preferred_language=language_code,
        onboarding_status="completed",
    )


async def reset_contact_onboarding(
    db,
    contact_id: str,
) -> Optional[Dict[str, Any]]:
    """Reset onboarding status to pending for language selection reset."""
    return await update_whatsapp_contact(
        db,
        contact_id,
        onboarding_status="pending",
    )


async def save_whatsapp_message(
    db,
    contact_id: str,
    direction: str,
    content: str,
    message_type: str = "text",
    media_url: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
    provider_message_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist an incoming or outgoing WhatsApp message."""
    msg_id = f"wamsg_{uuid.uuid4().hex[:12]}"
    now = _get_utc_now()
    meta_str = json.dumps(metadata_json) if metadata_json is not None else "{}"

    await db.execute(
        """
        INSERT INTO whatsapp_messages (
            id, contact_id, direction, message_type, content, media_url, metadata_json, provider_message_id, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        msg_id,
        contact_id,
        direction,
        message_type,
        content,
        media_url,
        meta_str,
        provider_message_id,
        now,
    )

    return {
        "id": msg_id,
        "contact_id": contact_id,
        "direction": direction,
        "message_type": message_type,
        "content": content,
        "media_url": media_url,
        "metadata_json": meta_str,
        "provider_message_id": provider_message_id,
        "created_at": now,
    }


async def get_whatsapp_message_history(
    db,
    contact_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve message history for a contact ordered chronologically."""
    rows = await db.fetch(
        """
        SELECT * FROM whatsapp_messages
        WHERE contact_id = $1
        ORDER BY created_at ASC
        LIMIT $2
        """,
        contact_id,
        limit,
    )
    return [dict(r) for r in rows]
