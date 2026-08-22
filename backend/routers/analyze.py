"""
analyze.py — document analysis router.

Cache hierarchy (fastest → slowest):
  L1  Redis      — sub-millisecond, TTL-based, shared across workers
  L2  SQLite     — persistent across restarts, used as fallback
  L3  Groq AI    — free tier (mixtral-8x7b), only called on true cache miss

Flow:
  POST /analyze
    ├─ L1 hit (Redis)   → 200 full result immediately
    ├─ L2 hit (SQLite)  → 200 full result + backfill Redis
    ├─ status=processing → 202 (background task already running)
    └─ miss             → queue background task → 202 { status: processing }

  GET /analyze/{id}/status  ← client polls every 3 s
    ├─ processing → { status: processing }
    ├─ done       → { status: done, analysis: {...} }
    └─ error      → { status: error, error: "..." }
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from cache import delete_analysis, get_analysis, set_analysis
from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import analyze_legal_document
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()
settings = get_settings()


# ── Sentry helpers ────────────────────────────────────────────────────────────

def _capture(exc: Exception, context: dict) -> None:
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            for k, v in context.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except ImportError:
        pass


def _breadcrumb(message: str, data: dict | None = None) -> None:
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            category="ai.pipeline",
            message=message,
            data=data or {},
            level="info",
        )
    except ImportError:
        pass


# ── Background worker ─────────────────────────────────────────────────────────

async def _upsert_analysis(db, analysis_id: str, document_id: str, payload: str, when: str) -> None:
    """Insert or update an analyses row keyed by the unique document_id.
    Portable across PostgreSQL (Supabase) and the SQLite fallback."""
    await db.execute(
        """INSERT INTO analyses (id, document_id, result_json, analyzed_at)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (document_id)
           DO UPDATE SET result_json = EXCLUDED.result_json,
                         analyzed_at = EXCLUDED.analyzed_at""",
        analysis_id, document_id, payload, when,
    )


async def _run_analysis(document_id: str, file_bytes: bytes, filename: str) -> None:
    """
    Runs after the HTTP response is sent.
    Writes status=processing → full result (or error) into the DB and Redis.
    Uses the shared DB pool so it works against Supabase PostgreSQL or the
    local SQLite fallback (never a hardcoded second database).
    """
    from database import get_db_ctx

    async with get_db_ctx() as db:
        # Mark as in-progress so the status endpoint can report it
        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await _upsert_analysis(db, analysis_id, document_id, json.dumps({"status": "processing"}), now)

        text = ""
        try:
            # ── Step 1: extract text ──────────────────────────────────────────
            _breadcrumb("pdf.extract.start", {"document_id": document_id, "bytes": len(file_bytes)})
            text = extract_text_from_pdf(file_bytes)
            _breadcrumb("pdf.extract.done", {"chars": len(text)})

            if not text.strip():
                raise ValueError(
                    "Could not extract text — make sure it is a text-based PDF, "
                    "not a scanned image."
                )

            print(f"[analyze] Extracted {len(text)} chars from '{filename}'")

            # ── Step 2: AI analysis (Groq) ────────────────────────────────────
            _breadcrumb("ai.analyze.start", {"filename": filename})
            analysis = await analyze_legal_document(text, filename)
            _breadcrumb(
                "ai.analyze.done",
                {
                    "clauses": len(analysis.get("clauses", [])),
                    "overall_risk": analysis.get("summary", {}).get("overall_risk"),
                },
            )

            analysis["document_id"] = document_id
            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            analysis["status"] = "done"

            # ── Step 3: persist result ────────────────────────────────────────
            await _upsert_analysis(db, analysis_id, document_id, json.dumps(analysis), analysis["analyzed_at"])
            doc_type = analysis.get("summary", {}).get("document_type", "")
            await db.execute(
                "UPDATE documents SET document_type = $1 WHERE id = $2",
                doc_type, document_id,
            )

            # ── Step 4: write to Redis (L1 cache) ────────────────────────────
            await set_analysis(document_id, analysis, ttl=settings.redis_cache_ttl)

            print(f"[analyze] Done — document_id={document_id}")

        except Exception as exc:
            _capture(
                exc,
                {
                    "document_id": document_id,
                    "filename": filename,
                    "text_chars": len(text),
                    "stage": "background_analysis",
                },
            )
            print(f"[analyze] FAILED {document_id}: {exc}")

            error_payload = json.dumps(
                {"status": "error", "error": str(exc), "document_id": document_id}
            )
            await _upsert_analysis(db, analysis_id, document_id, error_payload, datetime.utcnow().isoformat())
            # Don't cache error results in Redis — let the user retry cleanly


# ── Schema ────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    document_id: str
    force_reanalyze: bool = False


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("")
@limiter.limit("5/minute")
async def analyze_document(
    request: Request,
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    # ── Verify ownership FIRST (before any cache read) ────────────────────────
    doc = await db.fetchrow("SELECT * FROM documents WHERE id = $1", req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to analyze this document.")

    if not req.force_reanalyze:

        # ── L1: Redis ─────────────────────────────────────────────────────────
        cached = await get_analysis(req.document_id)
        if cached:
            status = cached.get("status")
            if status == "processing":
                return {"status": "processing", "document_id": req.document_id}
            if status == "error":
                raise HTTPException(
                    status_code=500,
                    detail=cached.get("error", "Analysis failed. Please try again."),
                )
            # Good result
            if len(cached.get("clauses", [])) > 0 or cached.get("summary", {}).get("total_clauses", 0) > 0:
                print(f"[analyze] L1 Redis HIT  document_id={req.document_id}")
                return {"analysis": cached}

        # ── L2: Database ──────────────────────────────────────────────────────
        row = await db.fetchrow(
            "SELECT result_json FROM analyses WHERE document_id = $1",
            req.document_id,
        )

        if row:
            db_result = json.loads(row["result_json"])
            status = db_result.get("status")

            if status == "processing":
                return {"status": "processing", "document_id": req.document_id}
            if status == "error":
                raise HTTPException(
                    status_code=500,
                    detail=db_result.get("error", "Analysis failed. Please try again."),
                )

            clause_count = len(db_result.get("clauses", []))
            total_clauses = db_result.get("summary", {}).get("total_clauses", 0)
            if clause_count > 0 or total_clauses > 0:
                print(f"[analyze] L2 DB HIT — backfilling Redis  document_id={req.document_id}")
                # Backfill Redis so the next request is served from L1
                await set_analysis(req.document_id, db_result, ttl=settings.redis_cache_ttl)
                return {"analysis": db_result}

    # ── Cache miss (or force_reanalyze) — clear stale entries ────────────────
    await delete_analysis(req.document_id)          # Redis
    await db.execute(                                # Database
        "DELETE FROM analyses WHERE document_id = $1", req.document_id
    )

    # ── Read file bytes ───────────────────────────────────────────────────────
    file_url = doc["file_url"]
    try:
        if file_url.startswith("local://"):
            local_path = file_url.replace("local://", "")
            with open(local_path, "rb") as f:
                file_bytes = f.read()
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url)
                file_bytes = resp.content
    except Exception as exc:
        _capture(exc, {"document_id": req.document_id, "file_url": file_url, "stage": "file_read"})
        raise HTTPException(status_code=500, detail=f"Could not read document: {exc}")

    # ── Queue background task — return 202 immediately ────────────────────────
    background_tasks.add_task(
        _run_analysis,
        document_id=req.document_id,
        file_bytes=file_bytes,
        filename=doc["filename"],
    )

    return {"status": "processing", "document_id": req.document_id}


@router.get("/{document_id}/status")
async def get_analysis_status(
    document_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Poll until status is 'done' or 'error'.
    Checks Redis first, falls back to SQLite.
    """
    # ── Verify ownership ───────────────────────────────────────────────────────
    doc = await db.fetchrow("SELECT user_id FROM documents WHERE id = $1", document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to access this document.")

    # L1: Redis
    cached = await get_analysis(document_id)
    if cached:
        status = cached.get("status", "done")
        if status == "processing":
            return {"status": "processing"}
        if status == "error":
            return {"status": "error", "error": cached.get("error", "Unknown error")}
        return {"status": "done", "analysis": cached}

    # L2: Database
    row = await db.fetchrow(
        "SELECT result_json FROM analyses WHERE document_id = $1", document_id
    )

    if not row:
        return {"status": "processing"}  # task not yet written anything

    result = json.loads(row["result_json"])
    status = result.get("status", "done")

    if status == "processing":
        return {"status": "processing"}
    if status == "error":
        return {"status": "error", "error": result.get("error", "Unknown error")}

    # Backfill Redis on the way out
    await set_analysis(document_id, result, ttl=settings.redis_cache_ttl)
    return {"status": "done", "analysis": result}


@router.delete("/{document_id}/cache")
async def clear_analysis_cache(
    document_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Evict from both Redis and the database so the document is re-analysed fresh."""
    # ── Verify ownership ───────────────────────────────────────────────────────
    doc = await db.fetchrow("SELECT user_id FROM documents WHERE id = $1", document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this document's cache.")

    await delete_analysis(document_id)
    await db.execute("DELETE FROM analyses WHERE document_id = $1", document_id)
    return {"message": "Cache cleared from Redis and database."}