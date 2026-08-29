"""Alembic migration environment.

The database URL is read from the app settings (DATABASE_URL) so migrations run
against the same database the app uses (Supabase PostgreSQL in production, or the
local SQLite fallback in development).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Make the backend package importable (config.py lives one level up).
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# We manage schema with explicit migrations, so no autogenerate metadata target.
target_metadata = None


def _database_url() -> str:
    url = get_settings().database_url.strip()
    # Normalise to a SQLAlchemy-compatible (sync) URL.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Supabase requires SSL for direct psycopg2 connections.
    if ("supabase.co" in url or "pooler.supabase.com" in url) and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
