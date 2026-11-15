"""initial schema

Captures the baseline schema (FKs declare ON DELETE CASCADE so fresh databases,
including SQLite which cannot ALTER constraints, match create_tables()). Uses CREATE TABLE IF NOT EXISTS so it is safe to run
against databases whose tables were already auto-created by the app's create_tables().

Revision ID: 0001
Revises:
Create Date: 2026-08-25
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    file_url      TEXT NOT NULL,
    file_size     INTEGER NOT NULL,
    document_type TEXT DEFAULT '',
    status        TEXT DEFAULT 'ready',
    uploaded_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analyses (
    id          TEXT PRIMARY KEY,
    document_id TEXT UNIQUE NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    result_json TEXT NOT NULL,
    analyzed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    timestamp   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS id_applications (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id_type TEXT NOT NULL, service TEXT NOT NULL,
    status TEXT DEFAULT 'in_progress', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS id_checklist_items (
    id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES id_applications(id) ON DELETE CASCADE,
    item_text TEXT NOT NULL, is_done INTEGER DEFAULT 0, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS property_applications (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_type TEXT NOT NULL, service TEXT NOT NULL,
    status TEXT DEFAULT 'in_progress', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS property_checklist_items (
    id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES property_applications(id) ON DELETE CASCADE,
    item_text TEXT NOT NULL, is_done INTEGER DEFAULT 0, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS business_applications (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_type TEXT NOT NULL, service TEXT NOT NULL,
    status TEXT DEFAULT 'in_progress', notes TEXT DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS business_checklist_items (
    id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES business_applications(id) ON DELETE CASCADE,
    item_text TEXT NOT NULL, is_done INTEGER DEFAULT 0, updated_at TEXT NOT NULL
);
"""


def upgrade() -> None:
    for stmt in filter(None, (s.strip() for s in SCHEMA.split(";"))):
        op.execute(stmt)


def downgrade() -> None:
    # Baseline migration — no destructive downgrade.
    pass
