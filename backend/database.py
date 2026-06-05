import aiosqlite
from config import get_settings

settings = get_settings()
DB_PATH = "smartlegal.db"


async def get_db():
    """Dependency — yields a DB connection per request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    """Create all tables on startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
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
        await db.commit()
