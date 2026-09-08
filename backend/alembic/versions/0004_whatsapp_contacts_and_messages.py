"""WhatsApp Contacts & Messages Persistence Schema

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create WhatsApp Contacts Table
    op.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_contacts (
            id                 TEXT PRIMARY KEY,
            phone_number       TEXT UNIQUE NOT NULL,
            user_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
            preferred_language TEXT DEFAULT NULL,
            onboarding_status  TEXT NOT NULL DEFAULT 'pending',
            created_at         TEXT NOT NULL,
            updated_at         TEXT NOT NULL
        )
    """)

    # 2. Create WhatsApp Messages History Table
    op.execute("""
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
        )
    """)

    # 3. Create Performance & Lookup Indexes
    indexes = [
        ("idx_whatsapp_contacts_phone", "whatsapp_contacts", "phone_number"),
        ("idx_whatsapp_contacts_user_id", "whatsapp_contacts", "user_id"),
        ("idx_whatsapp_messages_contact_id", "whatsapp_messages", "contact_id"),
        ("idx_whatsapp_messages_contact_time", "whatsapp_messages", "contact_id, created_at"),
        ("idx_whatsapp_messages_provider_id", "whatsapp_messages", "provider_message_id"),
    ]
    for idx_name, table_name, cols in indexes:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_whatsapp_messages_provider_id")
    op.execute("DROP INDEX IF EXISTS idx_whatsapp_messages_contact_time")
    op.execute("DROP INDEX IF EXISTS idx_whatsapp_messages_contact_id")
    op.execute("DROP INDEX IF EXISTS idx_whatsapp_contacts_user_id")
    op.execute("DROP INDEX IF EXISTS idx_whatsapp_contacts_phone")
    op.execute("DROP TABLE IF EXISTS whatsapp_messages")
    op.execute("DROP TABLE IF EXISTS whatsapp_contacts")
