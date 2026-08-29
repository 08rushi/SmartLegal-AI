"""auth hardening: token_version + password_resets

Adds session-revocation support (users.token_version) and the password-reset
table. Written for PostgreSQL (production); uses IF [NOT] EXISTS so it is safe to
re-run and safe on databases where the app already added these via create_tables().

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 0")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id),
            token_hash  TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            used        INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_password_resets_token_hash ON password_resets (token_hash)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS password_resets")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS token_version")
