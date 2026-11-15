"""Bring Alembic to parity with database.create_tables()

Adds everything create_tables() creates that migrations 0001-0005 did not:
  * documents.file_hash + idx_documents_file_hash
  * analysis_jobs (+ index)
  * whatsapp_conversation_context, whatsapp_message_processing,
    whatsapp_outbound_messages (+ indexes)
PostgreSQL only (SQLite cannot ALTER constraints/types; fresh SQLite DBs already get
the right shape from the edited 0001/0002/0005):
  * ON DELETE CASCADE on documents.user_id and password_resets.user_id
  * shadow_* timestamp columns TIMESTAMPTZ -> TEXT (the app writes ISO strings,
    which asyncpg rejects for timestamptz)

Idempotent: every step uses IF NOT EXISTS or inspects the live schema, so it is safe
on databases that create_tables() already populated.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


NEW_TABLES = """
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id              TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    stage           TEXT NOT NULL,
    progress_pct    INTEGER DEFAULT 0,
    retries         INTEGER DEFAULT 0,
    error_message   TEXT DEFAULT '',
    started_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whatsapp_conversation_context (
    id                          TEXT PRIMARY KEY,
    contact_id                  TEXT UNIQUE NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
    active_document_id          TEXT REFERENCES documents(id) ON DELETE SET NULL,
    workflow_state              TEXT NOT NULL DEFAULT 'idle',
    pending_candidates_json     TEXT NOT NULL DEFAULT '[]',
    draft_type                  TEXT DEFAULT NULL,
    draft_requirements_json     TEXT NOT NULL DEFAULT '{}',
    draft_confirmation_status   TEXT DEFAULT NULL,
    context_status              TEXT NOT NULL DEFAULT 'active',
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whatsapp_message_processing (
    id                      TEXT PRIMARY KEY,
    provider_message_id     TEXT UNIQUE NOT NULL,
    contact_id              TEXT NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
    processing_status       TEXT NOT NULL DEFAULT 'processing',
    attempt_count           INTEGER DEFAULT 1,
    started_at              TEXT NOT NULL,
    completed_at            TEXT DEFAULT NULL,
    outbound_reply          TEXT DEFAULT NULL,
    last_error_code         TEXT DEFAULT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whatsapp_outbound_messages (
    id                          TEXT PRIMARY KEY,
    idempotency_key             TEXT UNIQUE NOT NULL,
    inbound_provider_message_id TEXT NOT NULL,
    contact_id                  TEXT NOT NULL REFERENCES whatsapp_contacts(id) ON DELETE CASCADE,
    recipient_phone             TEXT NOT NULL,
    provider                    TEXT NOT NULL DEFAULT 'meta_cloud_api',
    message_type                TEXT NOT NULL DEFAULT 'text',
    outbound_payload_json       TEXT NOT NULL,
    delivery_status             TEXT NOT NULL DEFAULT 'pending',
    send_claim_id               TEXT NOT NULL,
    sending_started_at          TEXT NOT NULL,
    provider_message_id         TEXT DEFAULT NULL,
    attempt_count               INTEGER DEFAULT 0,
    last_error_code             TEXT DEFAULT NULL,
    last_error_class            TEXT DEFAULT NULL,
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL
);
"""

INDEXES = [
    ("idx_documents_file_hash", "documents", "user_id, file_hash"),
    ("idx_analysis_jobs_doc_id", "analysis_jobs", "document_id"),
    ("idx_wac_context_contact", "whatsapp_conversation_context", "contact_id"),
    ("idx_wac_context_doc", "whatsapp_conversation_context", "active_document_id"),
    ("idx_wmp_provider_msg", "whatsapp_message_processing", "provider_message_id"),
    ("idx_wmp_contact", "whatsapp_message_processing", "contact_id"),
    ("idx_wom_idempotency", "whatsapp_outbound_messages", "idempotency_key"),
    ("idx_wom_inbound_msg", "whatsapp_outbound_messages", "inbound_provider_message_id"),
    ("idx_wom_contact", "whatsapp_outbound_messages", "contact_id"),
    # Also created by 0002; repeated here so create_tables() and Alembic agree.
    ("ix_password_resets_token_hash", "password_resets", "token_hash"),
]


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. documents.file_hash (inspect: SQLite lacks ADD COLUMN IF NOT EXISTS)
    doc_cols = {c["name"] for c in insp.get_columns("documents")}
    if "file_hash" not in doc_cols:
        op.execute("ALTER TABLE documents ADD COLUMN file_hash TEXT DEFAULT ''")

    # 2. New tables
    for stmt in filter(None, (s.strip() for s in NEW_TABLES.split(";"))):
        op.execute(stmt)

    # 3. Indexes
    for idx_name, table_name, cols in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})")

    # 4. PostgreSQL-only constraint / type reconciliation
    if bind.dialect.name == "postgresql":
        for table in ("documents", "password_resets"):
            op.execute(
                f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_user_id_fkey, "
                f"ADD CONSTRAINT {table}_user_id_fkey FOREIGN KEY (user_id) "
                f"REFERENCES users(id) ON DELETE CASCADE"
            )
        insp = sa.inspect(bind)
        for table, cols in (
            ("shadow_analyses", ("started_at", "completed_at", "created_at")),
            ("shadow_comparisons", ("created_at",)),
        ):
            existing = {c["name"]: c for c in insp.get_columns(table)}
            for col in cols:
                info = existing.get(col)
                if info is not None and isinstance(info["type"], sa.DateTime):
                    op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")
                    op.execute(
                        f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TEXT USING {col}::text"
                    )


def downgrade() -> None:
    # Non-destructive: dropping these would discard WhatsApp state and job history.
    for idx_name, _t, _c in INDEXES:
        if idx_name != "ix_password_resets_token_hash":
            op.execute(f"DROP INDEX IF EXISTS {idx_name}")
