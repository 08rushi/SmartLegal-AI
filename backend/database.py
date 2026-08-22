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

    async with _db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                filename        TEXT NOT NULL,
                file_url        TEXT NOT NULL,
                file_size       INTEGER NOT NULL,
                document_type   TEXT DEFAULT '',
                status          TEXT DEFAULT 'ready',
                uploaded_at     TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id              TEXT PRIMARY KEY,
                document_id     TEXT UNIQUE NOT NULL,
                result_json     TEXT NOT NULL,
                analyzed_at     TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id              TEXT PRIMARY KEY,
                document_id     TEXT NOT NULL,
                user_id         TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS id_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                id_type         TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS id_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (application_id) REFERENCES id_applications(id)
            );

            CREATE TABLE IF NOT EXISTS property_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                property_type   TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS property_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (application_id) REFERENCES property_applications(id)
            );

            CREATE TABLE IF NOT EXISTS business_applications (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                business_type   TEXT NOT NULL,
                service         TEXT NOT NULL,
                status          TEXT DEFAULT 'in_progress',
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS business_checklist_items (
                id              TEXT PRIMARY KEY,
                application_id  TEXT NOT NULL,
                item_text       TEXT NOT NULL,
                is_done         INTEGER DEFAULT 0,
                updated_at      TEXT NOT NULL,
                FOREIGN KEY (application_id) REFERENCES business_applications(id)
            );
        """)
