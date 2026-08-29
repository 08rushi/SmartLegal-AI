"""Schema Authority, Drift Reconciliation, Native Types, Indexes & Foreign Key Cascades

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create / Reconcile Document Insights
    op.execute("""
        CREATE TABLE IF NOT EXISTS document_insights (
            id              TEXT PRIMARY KEY,
            document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            kind            TEXT NOT NULL,
            result_json     TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            UNIQUE (document_id, kind)
        )
    """)

    # 2. Create / Reconcile Jan-Yojana Central & State Schemes
    op.execute("""
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
        )
    """)

    # 3. Create / Reconcile Jan-Yojana AI Blogs
    op.execute("""
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
        )
    """)

    # 4. Alter Existing FK Constraints for ON DELETE CASCADE (SL-005)
    cascade_alters = [
        "ALTER TABLE id_applications DROP CONSTRAINT IF EXISTS id_applications_user_id_fkey, ADD CONSTRAINT id_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE property_applications DROP CONSTRAINT IF EXISTS property_applications_user_id_fkey, ADD CONSTRAINT property_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE business_applications DROP CONSTRAINT IF EXISTS business_applications_user_id_fkey, ADD CONSTRAINT business_applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE id_checklist_items DROP CONSTRAINT IF EXISTS id_checklist_items_application_id_fkey, ADD CONSTRAINT id_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES id_applications(id) ON DELETE CASCADE",
        "ALTER TABLE property_checklist_items DROP CONSTRAINT IF EXISTS property_checklist_items_application_id_fkey, ADD CONSTRAINT property_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES property_applications(id) ON DELETE CASCADE",
        "ALTER TABLE business_checklist_items DROP CONSTRAINT IF EXISTS business_checklist_items_application_id_fkey, ADD CONSTRAINT business_checklist_items_application_id_fkey FOREIGN KEY (application_id) REFERENCES business_applications(id) ON DELETE CASCADE",
        "ALTER TABLE analyses DROP CONSTRAINT IF EXISTS analyses_document_id_fkey, ADD CONSTRAINT analyses_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE",
        "ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_document_id_fkey, ADD CONSTRAINT chat_messages_document_id_fkey FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE"
    ]
    for alter_sql in cascade_alters:
        try:
            op.execute(alter_sql)
        except Exception:
            pass

    # 5. Performance B-Tree Indexes (SL-004)
    indexes = [
        ("idx_documents_user_id", "documents", "user_id"),
        ("idx_chat_messages_doc_time", "chat_messages", "document_id, timestamp"),
        ("idx_analyses_doc_id", "analyses", "document_id"),
        ("idx_id_applications_user_id", "id_applications", "user_id"),
        ("idx_property_applications_user_id", "property_applications", "user_id"),
        ("idx_business_applications_user_id", "business_applications", "user_id"),
        ("idx_yojana_schemes_cat_state", "yojana_schemes", "category, state_name"),
        ("idx_yojana_blogs_slug", "yojana_blogs", "slug"),
    ]
    for idx_name, table_name, cols in indexes:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})")



def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_yojana_blogs_slug")
    op.execute("DROP INDEX IF EXISTS idx_yojana_schemes_cat_state")
    op.execute("DROP INDEX IF EXISTS idx_business_applications_user_id")
    op.execute("DROP INDEX IF EXISTS idx_property_applications_user_id")
    op.execute("DROP INDEX IF EXISTS idx_id_applications_user_id")
    op.execute("DROP INDEX IF EXISTS idx_analyses_doc_id")
    op.execute("DROP INDEX IF EXISTS idx_chat_messages_doc_time")
    op.execute("DROP INDEX IF EXISTS idx_documents_user_id")
    op.execute("DROP TABLE IF EXISTS yojana_blogs")
    op.execute("DROP TABLE IF EXISTS yojana_schemes")
    op.execute("DROP TABLE IF EXISTS document_insights")
