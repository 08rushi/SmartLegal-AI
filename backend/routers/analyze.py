"""
analyze.py — document analysis router  (SL-009 / SL-011 / SL-012).

Cache hierarchy (fastest → slowest):
  L1  Redis      — sub-millisecond, TTL-based, shared across workers
  L2  PostgreSQL — persistent across restarts, used as fallback
  L3  Groq AI    — only called on true cache miss

Job dispatch  (SL-012):
  When REDIS_URL is set, analysis jobs are dispatched to the persistent
  ARQ worker (`arq worker worker.WorkerSettings`) so they survive restarts.
  When REDIS_URL is absent (dev mode), jobs run via asyncio.create_task,
  preserving the previous BackgroundTasks behaviour.

Flow:
  POST /analyze
    ├─ L1 hit (Redis)    → 200 full result immediately
    ├─ L2 hit (Database) → 200 full result + backfill Redis
    ├─ status=processing → 202 (worker already running)
    └─ miss              → enqueue ARQ job → 202 { status: processing }

  GET /analyze/{id}/status  ← client polls every 3 s
    ├─ processing → { status: processing }
    ├─ done       → { status: done, analysis: {...} }
    └─ error      → { status: error, error: "..." }
"""

import asyncio
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from cache import delete_analysis, get_analysis, set_analysis, set_doc_text
from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.analysis_schema import validate_analysis
from services.groq_service import analyze_legal_document
from services.pdf_parser import extract_text_from_pdf, assess_readability
from services.page_content import PageContentList
from services.vision_pipeline import VisualDocumentPipeline
from services.ocr_service import ocr_available, ocr_image_bytes, ocr_pdf_scanned
from services.document_inspector import DocumentSuitabilityInspector
from services.adaptive_optimizer import AdaptiveOptimizationEngine, OptimizationTelemetry
from services.page_splitter import DeterministicPageSplitter, recombine_pages

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

    scratch_dir = os.path.join(tempfile.gettempdir(), f"sl_opt_{document_id}_{uuid.uuid4().hex[:6]}")
    optimization_telemetry: Optional[OptimizationTelemetry] = None

    async with get_db_ctx() as db:
        # Mark as in-progress so the status endpoint can report it. `started_at`
        # lets the reaper detect jobs orphaned by a worker restart.
        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await _upsert_analysis(
            db, analysis_id, document_id,
            json.dumps({"status": "processing", "started_at": now}), now,
        )

        text = ""
        try:
            # ── Step 1: Document Inspection, Optimization & Text extraction ────
            _breadcrumb("pdf.extract.start", {"document_id": document_id, "bytes": len(file_bytes)})
            is_pdf = file_bytes[:5].startswith(b"%PDF")

            inspector = DocumentSuitabilityInspector()
            profile = inspector.inspect(file_bytes, filename)
            optimizer = AdaptiveOptimizationEngine()

            if is_pdf and profile.recommended_strategy == "page_split":
                splitter = DeterministicPageSplitter(max_pages_per_part=20)
                parts = splitter.split(file_bytes, document_id=document_id)
                part_results = []
                for part in parts:
                    part_bytes, _ = optimizer.optimize(part.content_bytes, filename)
                    part_pages = extract_text_from_pdf(part_bytes)
                    if part_pages.document_type in ("scanned_pdf", "mixed_pdf") or not assess_readability(part_pages.to_text())["readable"]:
                        can_visual = ocr_available() or (settings.cloud_vision_enabled and not settings.privacy_mode and bool(settings.gemini_api_key))
                        if can_visual:
                            pipeline = VisualDocumentPipeline()
                            transcriptions = await asyncio.wait_for(
                                pipeline.process_pdf_pages(part_bytes, part_pages),
                                timeout=settings.analysis_timeout_seconds,
                            )
                            part_pages = PageContentList([t.to_page_content() for t in transcriptions])
                            part_quality = assess_readability(part_pages.to_text())
                            if not part_quality["readable"]:
                                raise ValueError(
                                    f"OCR could not recover enough readable text from pages {part.start_page}-{part.end_page}. "
                                    "Please upload a clearer scan or enable a supported OCR provider."
                                )
                        else:
                            raise ValueError(
                                f"Pages {part.start_page}-{part.end_page} appear to be scanned images, but OCR is unavailable. "
                                "Install/configure Tesseract or enable Gemini Vision, then re-upload the document."
                            )
                    part_results.append((part, part_pages))
                pages = recombine_pages(part_results)
                text = pages.to_text()
                doc_type = pages.document_type
                quality = assess_readability(text)
                if not quality["readable"]:
                    raise ValueError(
                        "The document was split for processing, but too little readable text was extracted. "
                        "For scanned PDFs, enable OCR or upload a clearer/searchable PDF."
                    )
                optimization_telemetry = OptimizationTelemetry(
                    original_size_bytes=len(file_bytes),
                    optimized_size_bytes=sum(p.file_size_bytes for p in parts),
                    optimization_applied=True,
                    optimization_method="page_split",
                    pages_optimized=len(pages),
                    pages_split=len(parts),
                    optimization_reason=profile.reason,
                    technical_quality_score=quality.get("quality_score", 1.0) if isinstance(quality, dict) else 1.0,
                    technical_readability_metrics={"parts": len(parts), "pages": len(pages)},
                )
            else:
                processing_bytes, optimization_telemetry = optimizer.optimize(file_bytes, filename, profile=profile)
                if is_pdf:
                    pages = extract_text_from_pdf(processing_bytes)
                    doc_type = pages.document_type
                    text = pages.to_text()
                    quality = assess_readability(text)
                    _breadcrumb("pdf.extract.done", {"chars": len(text), "pages": len(pages), "doc_type": doc_type, "readable": quality["readable"]})
                    print(f"[analyze] Extracted {len(pages)} pages from '{filename}' | document_type={doc_type} | readable={quality['readable']}")

                    # No usable text layer → it's a scan / non-Unicode PDF → try OCR.
                    has_unclear_or_scanned = not quality["readable"] or doc_type in ("scanned_pdf", "mixed_pdf")
                    if has_unclear_or_scanned:
                        can_visual = ocr_available() or (settings.cloud_vision_enabled and not settings.privacy_mode and bool(settings.gemini_api_key))
                        if can_visual:
                            print(f"[analyze] Running Visual / OCR Pipeline on '{filename}' (doc_type={doc_type})…")
                            _breadcrumb("ocr.pdf.start", {"document_id": document_id})
                            pipeline = VisualDocumentPipeline()
                            transcriptions = await asyncio.wait_for(
                                pipeline.process_pdf_pages(processing_bytes, pages),
                                timeout=settings.analysis_timeout_seconds,
                            )
                            pages = PageContentList([t.to_page_content() for t in transcriptions])
                            text = pages.to_text()
                            quality = assess_readability(text)
                            _breadcrumb("ocr.pdf.done", {"chars": len(text), "readable": quality["readable"]})
                            if not quality["readable"]:
                                raise ValueError(
                                    "We couldn't read enough text from this scanned PDF even "
                                    "with OCR. Please upload a clearer, higher-resolution scan "
                                    "(300 DPI, well-lit and straight), or a text-based PDF."
                                )
                        else:
                            raise ValueError(
                                "This looks like a scanned image or photo saved as a PDF, and "
                                "OCR is not enabled on the server. Please upload a text-based "
                                "PDF (where the text can be selected/copied), or ask the admin "
                                "to enable OCR (install Tesseract)."
                            )
                else:
                    can_visual = ocr_available() or (settings.cloud_vision_enabled and not settings.privacy_mode and bool(settings.gemini_api_key))
                    if not can_visual:
                        raise ValueError(
                            "This is an image document, and OCR is not enabled on the server "
                            "yet, so we can't read text from images. Please upload a text-based "
                            "PDF, or ask the admin to enable OCR (install Tesseract)."
                        )
                    print(f"[analyze] Image document '{filename}' → running Visual / OCR Pipeline…")
                    _breadcrumb("ocr.image.start", {"document_id": document_id})
                    pipeline = VisualDocumentPipeline()
                    transcriptions = await asyncio.wait_for(
                        pipeline.process_image_file(processing_bytes, filename),
                        timeout=settings.analysis_timeout_seconds,
                    )
                    pages = PageContentList([t.to_page_content() for t in transcriptions])
                    text = pages.to_text()
                    quality = assess_readability(text)
                    _breadcrumb("ocr.image.done", {"chars": len(text), "readable": quality["readable"]})
                    if not quality["readable"]:
                        raise ValueError(
                            "We couldn't read enough text from this image. Please upload a "
                            "clearer, well-lit, straight photo or scan (300 DPI works best), "
                            "or a text-based PDF."
                        )

            if not text or not quality.get("readable", False):
                raise ValueError(
                    "No sufficiently readable text could be extracted from this document. "
                    "If it is scanned, enable OCR; otherwise upload a valid text-based PDF or a clearer image."
                )

            print(f"[analyze] Extracted {len(text)} chars from '{filename}' | script={quality.get('script')}")

            # Cache the extracted text so chat doesn't re-parse the PDF later.
            await set_doc_text(document_id, text, ttl=settings.redis_cache_ttl)

            # ── Step 2: AI analysis (Groq) — bounded so a hung call can't hang forever
            _breadcrumb("ai.analyze.start", {"filename": filename})
            analysis = await asyncio.wait_for(
                analyze_legal_document(text, filename),
                timeout=settings.analysis_timeout_seconds,
            )
            # Validate & normalize the model output before trusting it.
            analysis = validate_analysis(analysis)

            # ── Step 2b: Attach version & optimization metadata (Phase 6) ─────
            meta = analysis.setdefault("metadata", {})
            meta["pipeline_version"] = "v1.0.0"
            meta["analyzed_at"] = datetime.utcnow().isoformat()
            if optimization_telemetry:
                meta["optimization"] = optimization_telemetry.to_dict()

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
            if isinstance(exc, asyncio.TimeoutError):
                message = "Analysis timed out. The document may be too large — please try again."
            else:
                message = str(exc) or "Analysis failed. Please try again."
            _capture(
                exc,
                {
                    "document_id": document_id,
                    "filename": filename,
                    "text_chars": len(text),
                    "stage": "background_analysis",
                },
            )
            print(f"[analyze] FAILED {document_id}: {message}")

            error_payload = json.dumps(
                {"status": "error", "error": message, "document_id": document_id}
            )
            await _upsert_analysis(db, analysis_id, document_id, error_payload, datetime.utcnow().isoformat())
            # Don't cache error results in Redis — let the user retry cleanly

        finally:
            # Deterministic derived artifact cleanup on both success and failure (Phase 6)
            if os.path.exists(scratch_dir):
                try:
                    shutil.rmtree(scratch_dir, ignore_errors=True)
                except Exception:
                    pass


# ── Reaper: fail analyses orphaned by a worker restart ────────────────────────

def _parse_iso(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


async def reap_stale_analyses(db) -> int:
    """
    Mark any analysis stuck in 'processing' longer than analysis_timeout_seconds as
    'error'. BackgroundTasks do not survive a worker restart, so without this a job
    interrupted mid-run would stay 'processing' forever. Returns how many were reaped.
    """
    timeout = settings.analysis_timeout_seconds
    now = datetime.now(timezone.utc)
    reaped = 0
    try:
        rows = await db.fetch(
            "SELECT id, document_id, result_json, analyzed_at FROM analyses "
            "WHERE result_json LIKE '%\"status\": \"processing\"%'"
        )
    except Exception as exc:
        print(f"[reaper] query failed: {exc}")
        return 0

    for row in rows:
        try:
            payload = json.loads(row["result_json"])
        except (TypeError, ValueError):
            continue
        if payload.get("status") != "processing":
            continue
        started = _parse_iso(payload.get("started_at") or row["analyzed_at"] or "")
        if started is None:
            continue
        # Big documents carry their own (longer) time budget; add slack for the final steps.
        row_timeout = (payload.get("timeout_seconds") or timeout) + 60
        if (now - started).total_seconds() <= row_timeout:
            continue  # still within the allowed window
        error_payload = json.dumps({
            "status": "error",
            "error": "Analysis did not finish (the server may have restarted). Please re-analyze.",
            "document_id": row["document_id"],
        })
        await _upsert_analysis(db, row["id"], row["document_id"], error_payload, now.isoformat())
        reaped += 1

    if reaped:
        print(f"[reaper] marked {reaped} stale analysis job(s) as error")
    return reaped


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
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    # ── Verify ownership FIRST (before any cache read) ────────────────────────
    doc = await db.fetchrow("SELECT * FROM documents WHERE id = $1", req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to analyze this document.")

    # Concurrency limit check (SL-016 abuse control)
    active_row = await db.fetchrow(
        """SELECT COUNT(*) AS active_count
           FROM analyses a
           JOIN documents d ON a.document_id = d.id
           WHERE d.user_id = $1 AND a.result_json LIKE '%"status": "processing"%'""",
        current_user["id"],
    )
    if active_row and active_row["active_count"] >= 3:
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent analysis requests. Please wait for your pending document analysis to finish.",
        )


    if not req.force_reanalyze:

        # ── L1: Redis ─────────────────────────────────────────────────────────
        cached = await get_analysis(req.document_id)
        if cached:
            status = cached.get("status")
            if status == "processing":
                # Redis can outlive a failed worker attempt. Only treat this as
                # an active job when the authoritative DB row also says processing.
                processing_row = await db.fetchrow(
                    "SELECT result_json FROM analyses WHERE document_id = $1",
                    req.document_id,
                )
                if not processing_row:
                    # Likely the brief interval between enqueue and worker startup.
                    return {"status": "processing", "document_id": req.document_id}
                try:
                    processing_result = json.loads(processing_row["result_json"])
                except (TypeError, ValueError):
                    processing_result = {}
                if processing_result.get("status") == "processing":
                    return {"status": "processing", "document_id": req.document_id}
                # DB says done/error: ignore stale Redis processing and continue
                # through the DB-result/re-dispatch logic below.
            # A cached "error" is a previous failed attempt (timeout, rate limit,
            # transient AI/provider error, etc). Don't replay it forever — fall
            # through and let the code below re-dispatch a fresh analysis instead
            # of permanently stamping this document as broken.
            if status != "error":
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

            clause_count = len(db_result.get("clauses", [])) if status != "error" else 0
            total_clauses = db_result.get("summary", {}).get("total_clauses", 0)
            if clause_count > 0 or total_clauses > 0:
                print(f"[analyze] L2 DB HIT — backfilling Redis  document_id={req.document_id}")
                await set_analysis(req.document_id, db_result, ttl=settings.redis_cache_ttl)
                return {"analysis": db_result}

    # ── Cache miss (or force_reanalyze) — clear stale entries ─────────────────
    await delete_analysis(req.document_id)          # Redis
    await db.execute(                                # Database
        "DELETE FROM analyses WHERE document_id = $1", req.document_id
    )

    # ── Read file bytes ────────────────────────────────────────────────────────
    file_url = doc["file_url"]
    try:
        if file_url.startswith("local://"):
            import os
            local_path = file_url.replace("local://", "")
            if not os.path.exists(local_path):
                raise HTTPException(
                    status_code=404,
                    detail="The original document file is no longer available on temporary server storage. Please re-upload the document to run a new analysis."
                )
            with open(local_path, "rb") as f:
                file_bytes = f.read()
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url)
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail="Could not retrieve the document file from remote storage."
                    )
                file_bytes = resp.content
    except HTTPException:
        raise
    except Exception as exc:
        _capture(exc, {"document_id": req.document_id, "file_url": file_url, "stage": "file_read"})
        raise HTTPException(status_code=500, detail=f"Could not read document: {exc}")

    # ── Dispatch to durable ARQ worker (SL-012) ────────────────────────────────
    from worker import enqueue_analysis
    job_id = await enqueue_analysis(
        document_id=req.document_id,
        file_bytes=file_bytes,
        filename=doc["filename"],
    )
    print(f"[analyze] Enqueued analysis job_id={job_id} for document_id={req.document_id}")

    # Phase 9: Non-blocking Shadow Execution Hook (completely isolated)
    try:
        from shadow.sampler import maybe_enqueue_shadow_analysis
        asyncio.create_task(
            maybe_enqueue_shadow_analysis(
                document_id=req.document_id,
                file_bytes=file_bytes,
                filename=doc["filename"],
                user_id=current_user["id"],
            )
        )
    except Exception as shadow_exc:
        # Non-negotiable: Shadow failures must never impact primary citizen experience
        print(f"[shadow] Gracefully bypassed shadow enqueue: {shadow_exc}")

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

    # The database is the source of truth for job state. Redis is only a cache:
    # a stale Redis `processing` entry must never hide a terminal DB error/result.
    row = await db.fetchrow(
        "SELECT result_json FROM analyses WHERE document_id = $1", document_id
    )

    if not row:
        # The worker may not have persisted its initial row yet. Only consult
        # Redis for this short dispatch race; do not let it override a DB row.
        cached = await get_analysis(document_id)
        if cached and cached.get("status") in ("done", "error", "processing"):
            if cached.get("status") == "error":
                return {"status": "error", "error": cached.get("error", "Unknown error")}
            if cached.get("status") == "done":
                return {"status": "done", "analysis": cached}
        return {"status": "processing"}

    result = json.loads(row["result_json"])
    status = result.get("status", "done")

    if status == "processing":
        # If this job is older than the timeout, the worker likely died — reap it now
        # so the client sees a clean error instead of polling forever.
        started = _parse_iso(result.get("started_at") or "")
        row_timeout = (result.get("timeout_seconds") or settings.analysis_timeout_seconds) + 60
        if started and (datetime.now(timezone.utc) - started).total_seconds() > row_timeout:
            message = "Analysis did not finish (the server may have restarted). Please re-analyze."
            await _upsert_analysis(
                db, str(uuid.uuid4()), document_id,
                json.dumps({"status": "error", "error": message, "document_id": document_id}),
                datetime.now(timezone.utc).isoformat(),
            )
            await set_analysis(document_id, {"status": "error", "error": message, "document_id": document_id}, ttl=settings.redis_cache_ttl)
            return {"status": "error", "error": message}
        # Live progress from the worker (ignore leftovers of a previous finished/failed run).
        job = await db.fetchrow(
            "SELECT stage, progress_pct FROM analysis_jobs WHERE document_id = $1", document_id
        )
        if job and job["stage"] not in ("completed", "failed"):
            return {"status": "processing", "stage": job["stage"], "progress_pct": job["progress_pct"]}
        return {"status": "processing"}
    if status == "error":
        # Refresh the cache with the authoritative terminal state, replacing
        # any old `processing` entry left behind by a previous worker attempt.
        await set_analysis(document_id, result, ttl=settings.redis_cache_ttl)
        return {"status": "error", "error": result.get("error", "Unknown error")}

    # Backfill/refresh Redis only with a completed DB result.
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