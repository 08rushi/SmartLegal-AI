from contextlib import asynccontextmanager
from urllib.parse import urlparse, unquote
from config import get_settings
import asyncpg
import aiosqlite
import re

settings = get_settings()

_db_pool = None
_is_sqlite = False
_sqlite_path = "smartlegal.db"


def _parse_db_url(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/postgres").lstrip("/"),
    }


class SQLiteConnectionWrapper:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        self._conn.row_factory = aiosqlite.Row

    def _convert_query(self, query: str, args: tuple) -> tuple[str, tuple]:
        if not args or '$' not in query:
            return query, args
        matches = [int(m) for m in re.findall(r'\$(\d+)', query)]
        if not matches:
            return query, args
        new_query = re.sub(r'\$\d+', '?', query)
        new_params = tuple(args[m - 1] for m in matches if 0 <= m - 1 < len(args))
        return new_query, new_params

    async def fetchrow(self, query: str, *args):
        q, params = self._convert_query(query, args)
        async with self._conn.execute(q, params) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def fetch(self, query: str, *args):
        q, params = self._convert_query(query, args)
        async with self._conn.execute(q, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def execute(self, query: str, *args):
        q, params = self._convert_query(query, args)
        if ";" in q and not args:
            await self._conn.executescript(q)
        else:
            await self._conn.execute(q, params)
        await self._conn.commit()

    async def commit(self):
        await self._conn.commit()


class SQLitePoolWrapper:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def acquire(self):
        async with aiosqlite.connect(self.db_path) as conn:
            yield SQLiteConnectionWrapper(conn)

    async def close(self):
        pass


async def init_db_pool():
    global _db_pool, _is_sqlite
    if _db_pool is not None:
        return

    url = settings.database_url.strip()
    if url.startswith("sqlite"):
        _is_sqlite = True
        _db_pool = SQLitePoolWrapper(_sqlite_path)
        await create_tables()
        return

    params = _parse_db_url(url)
    use_ssl = "supabase.co" in url or "pooler.supabase.com" in url

    try:
        _db_pool = await asyncpg.create_pool(
            **params,
            min_size=2,
            max_size=10,
            command_timeout=60,
            **({"ssl": "require"} if use_ssl else {}),
        )
        await create_tables()
        _is_sqlite = False
    except Exception as exc:
        print(f"[DB] PostgreSQL unavailable: {exc}. Using local SQLite database (smartlegal.db)")
        _is_sqlite = True
        _db_pool = SQLitePoolWrapper(_sqlite_path)
        await create_tables()


async def init_db():
    await init_db_pool()


async def close_db_pool():
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


async def get_db():
    if _db_pool is None:
        await init_db_pool()
    async with _db_pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_db_ctx():
    if _db_pool is None:
        await init_db_pool()
    async with _db_pool.acquire() as conn:
        yield conn


async def create_tables():
    global _db_pool
    if _db_pool is None:
        return

    # In production, log schema authority notice
    if getattr(settings, 'env', 'development') == 'production':
        print("[DB] Production environment detected: Database schema is governed by Alembic migrations.")

    async with _db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                password      TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                token_version INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS password_resets (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash  TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                used        INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename        TEXT NOT NULL,
                file_url        TEXT NOT NULL,
                file_size       INTEGER NOT NULL,
                document_type   TEXT DEFAULT '',
                file_hash       TEXT DEFAULT '',
                status          TEXT DEFAULT 'ready',
                uploaded_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(user_id, file_hash);


            CREATE TABLE IF NOT EXISTS analyses (
                id              TEXT PRIMARY KEY,
                document_id     TEXT UNIQUE NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                result_json     TEXT NOT NULL,
                analyzed_at     TEXT NOT NULL
            );

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
            CREATE INDEX IF NOT EXISTS idx_analysis_jobs_doc_id ON analysis_jobs(document_id);


            CREATE TABLE IF NOT EXISTS chat_messages (
                id              TEXT PRIMARY KEY,
                document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                user_id         TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                timestamp       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS document_insights (
                id              TEXT PRIMARY KEY,
                document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                kind            TEXT NOT NULL,
                result_json     TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                UNIQUE (document_id, kind)
            );

            CREATE TABLE IF NOT EXISTS id_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                id_type         TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS id_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL REFERENCES id_applications(id) ON DELETE CASCADE,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS property_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                property_type   TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS property_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL REFERENCES property_applications(id) ON DELETE CASCADE,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS business_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                business_type   TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS business_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL REFERENCES business_applications(id) ON DELETE CASCADE,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS yojana_schemes (
                id                  TEXT PRIMARY KEY,
                scheme_code         TEXT UNIQUE NOT NULL,
                title               TEXT NOT NULL,
                government_level    TEXT NOT NULL,
                state_name          TEXT DEFAULT 'ALL',
                category            TEXT NOT NULL,
                summary_english     TEXT NOT NULL,
                summary_hindi       TEXT NOT NULL,
                benefits_json       TEXT NOT NULL,
                eligibility_json    TEXT NOT NULL,
                required_docs_json  TEXT NOT NULL,
                official_portal_url TEXT NOT NULL,
                last_updated_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS yojana_blogs (
                id                  TEXT PRIMARY KEY,
                scheme_id           TEXT REFERENCES yojana_schemes(id) ON DELETE SET NULL,
                title               TEXT NOT NULL,
                slug                TEXT UNIQUE NOT NULL,
                summary             TEXT NOT NULL,
                content_markdown    TEXT NOT NULL,
                image_url           TEXT NOT NULL,
                official_links_json TEXT NOT NULL,
                published_at        TEXT NOT NULL
            );
        """)

        # Performance B-Tree indexes (SL-004) & FK Cascades (SL-005)
        index_statements = [
            "ALTER TABLE id_applications DROP CONSTRAINT IF EXISTS id_applications_user_id_fkey, ADD CONSTRAINT id_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
            "ALTER TABLE property_applications DROP CONSTRAINT IF EXISTS property_applications_user_id_fkey, ADD CONSTRAINT property_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
            "ALTER TABLE business_applications DROP CONSTRAINT IF EXISTS business_applications_user_id_fkey, ADD CONSTRAINT business_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
            "ALTER TABLE id_checklist_items DROP CONSTRAINT IF EXISTS id_checklist_items_application_id_fkey, ADD CONSTRAINT id_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES id_applications(id) ON DELETE CASCADE",
            "ALTER TABLE property_checklist_items DROP CONSTRAINT IF EXISTS property_checklist_items_application_id_fkey, ADD CONSTRAINT property_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES property_applications(id) ON DELETE CASCADE",
            "ALTER TABLE business_checklist_items DROP CONSTRAINT IF EXISTS business_checklist_items_application_id_fkey, ADD CONSTRAINT business_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES business_applications(id) ON DELETE CASCADE",
            "ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0",
            "CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_doc_time ON chat_messages(document_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_doc_id ON analyses(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_id_applications_user_id ON id_applications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_property_applications_user_id ON property_applications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_business_applications_user_id ON business_applications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_yojana_schemes_cat_state ON yojana_schemes(category, state_name)",
            "CREATE INDEX IF NOT EXISTS idx_yojana_blogs_slug ON yojana_blogs(slug)",
        ]
        for stmt in index_statements:
            try:
                await conn.execute(stmt)
            except Exception:
                pass  # constraint/column/index already exists



