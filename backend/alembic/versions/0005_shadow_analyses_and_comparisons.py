"""Shadow Analyses & Comparisons Persistence Schema (Phase 9)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create shadow_analyses table
    op.execute("""
        CREATE TABLE IF NOT EXISTS shadow_analyses (
            id                      TEXT PRIMARY KEY,
            experiment_id           TEXT NOT NULL,
            document_id             TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            candidate_provider      TEXT NOT NULL,
            candidate_model         TEXT NOT NULL,
            candidate_version       TEXT NOT NULL,
            source_document_hash    TEXT NOT NULL,
            result_json             TEXT NOT NULL,
            execution_status        TEXT NOT NULL,
            failure_category        TEXT,
            prompt_tokens           INTEGER DEFAULT 0,
            completion_tokens       INTEGER DEFAULT 0,
            estimated_cost_usd      REAL DEFAULT 0.0,
            started_at              TIMESTAMP WITH TIME ZONE NOT NULL,
            completed_at            TIMESTAMP WITH TIME ZONE NOT NULL,
            latency_ms              INTEGER NOT NULL,
            rollout_stage           TEXT DEFAULT 'shadow',
            created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_exp_doc UNIQUE (experiment_id, document_id)
        )
    """)

    # 2. Create shadow_comparisons table
    op.execute("""
        CREATE TABLE IF NOT EXISTS shadow_comparisons (
            id                      TEXT PRIMARY KEY,
            experiment_id           TEXT NOT NULL,
            document_id             TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            primary_analysis_id     TEXT,
            shadow_analysis_id      TEXT REFERENCES shadow_analyses(id) ON DELETE CASCADE,
            cer                     REAL DEFAULT 0.0,
            wer                     REAL DEFAULT 0.0,
            risk_concordance        REAL DEFAULT 0.0,
            citation_recall         REAL DEFAULT 0.0,
            sequence_similarity     REAL DEFAULT 0.0,
            latency_delta_ms        INTEGER DEFAULT 0,
            token_delta             INTEGER DEFAULT 0,
            cost_delta_usd          REAL DEFAULT 0.0,
            metrics_json            TEXT DEFAULT '{}',
            created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_comparison UNIQUE (experiment_id, document_id)
        )
    """)

    # 3. Create Performance & Lookup Indexes
    indexes = [
        ("idx_shadow_analyses_exp_doc", "shadow_analyses", "experiment_id, document_id"),
        ("idx_shadow_analyses_doc_id", "shadow_analyses", "document_id"),
        ("idx_shadow_comparisons_exp_doc", "shadow_comparisons", "experiment_id, document_id"),
        ("idx_shadow_comparisons_doc_id", "shadow_comparisons", "document_id"),
    ]
    for idx_name, table_name, cols in indexes:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_shadow_comparisons_doc_id")
    op.execute("DROP INDEX IF EXISTS idx_shadow_comparisons_exp_doc")
    op.execute("DROP TABLE IF EXISTS shadow_comparisons")
    op.execute("DROP INDEX IF EXISTS idx_shadow_analyses_doc_id")
    op.execute("DROP INDEX IF EXISTS idx_shadow_analyses_exp_doc")
    op.execute("DROP TABLE IF EXISTS shadow_analyses")
