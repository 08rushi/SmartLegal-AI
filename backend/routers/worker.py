"""
worker.py — Durable ARQ analysis worker  (SL-012).

This module defines:
  1. The ARQ job function `run_analysis_job` — the same logic that was
     formerly in analyze.py `_run_analysis`, moved here so it lives inside
     a proper worker process that survives FastAPI restarts.
  2. `WorkerSettings` — the ARQ class consumed by `arq worker worker.WorkerSettings`.
  3. A helper `enqueue_analysis` used by the HTTP router to submit jobs.

ARQ features we rely on:
  • Durable jobs — job state stored in Redis; survives process restarts.
  • Automatic retries  — configurable via `max_tries`.
  • Deduplication — controlled via `job_id`.
  • Timeout enforcement — `job_timeout` matches analysis_timeout_seconds.

Graceful degradation:
  If REDIS_URL is not configured, `enqueue_analysis` falls back to a direct
  asyncio coroutine call (the old BackgroundTasks behaviour) so the app
  keeps working in dev without Redis.
"""

import asyncio
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

from config import get_settings

settings = get_settings()


# ── Sentry helpers (no-op when sentry-sdk not installed) ─────────────────────

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


# ── DB helper ─────────────────────────────────────────────────────────────────

async def _upsert_analysis(db, analysis_id: str, document_id: str, payload: str, when: str) -> None:
    """Insert or update an analyses row, compatible with PostgreSQL and SQLite."""
    await db.execute(
        """INSERT INTO analyses (id, document_id, result_json, analyzed_at)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (document_id)
           DO UPDATE SET result_json = EXCLUDED.result_json,
                         analyzed_at = EXCLUDED.analyzed_at""",
        analysis_id, document_id, payload, when,
    )


async def _update_job_stage(db, document_id: str, stage: str, progress_pct: int, error_message: str = "") -> None:
    """Track analysis job progress lifecycle in analysis_jobs table (SL-025)."""
    job_id = f"job_{document_id}"
    now = datetime.utcnow().isoformat()
    await db.execute(
        """INSERT INTO analysis_jobs (id, document_id, stage, progress_pct, retries, error_message, started_at, updated_at)
           VALUES ($1, $2, $3, $4, 0, $5, $6, $6)
           ON CONFLICT (id)
           DO UPDATE SET stage = EXCLUDED.stage,
                         progress_pct = EXCLUDED.progress_pct,
                         error_message = EXCLUDED.error_message,
                         updated_at = EXCLUDED.updated_at""",
        job_id, document_id, stage, progress_pct, error_message, now,
    )


# ── Core analysis logic (extracted from analyze.py) ───────────────────────────

async def _execute_analysis(document_id: str, file_bytes: bytes, filename: str) -> None:
    """
    Full AI analysis pipeline — runs inside worker process independent of FastAPI lifespan.
    Tracks job stage transitions, enriches verified legal references, and attaches version metadata.
    """
    from database import get_db_ctx
    from cache import set_analysis, set_doc_text
    from services.pdf_parser import extract_text_from_pdf, assess_readability
    from services.page_content import PageContentList
    from services.vision_pipeline import VisualDocumentPipeline
    from services.ocr_service import ocr_available, ocr_image_bytes, ocr_pdf_scanned
    from services.groq_service import analyze_legal_document
    from services.analysis_schema import validate_analysis
    from services.legal_reference_service import enrich_clause_citations
    from services.prompt_registry import PROMPT_VERSION
    from services.document_inspector import DocumentSuitabilityInspector
    from services.adaptive_optimizer import AdaptiveOptimizationEngine, OptimizationTelemetry
    from services.page_splitter import DeterministicPageSplitter, recombine_pages

    scratch_dir = os.path.join(tempfile.gettempdir(), f"sl_opt_{document_id}_{uuid.uuid4().hex[:6]}")
    optimization_telemetry: Optional[OptimizationTelemetry] = None

    async with get_db_ctx() as db:
        # ── Step 0: Initialise job tracking ───────────────────────────────────
        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        await _update_job_stage(db, document_id, "extracting", 20)
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
                    part_doc_type = getattr(part_pages, "document_type", "digital_pdf")
                    part_text = part_pages.to_text() if hasattr(part_pages, "to_text") else str(part_pages)
                    if part_doc_type in ("scanned_pdf", "mixed_pdf") or not assess_readability(part_text)["readable"]:
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
                text = pages.to_text() if hasattr(pages, "to_text") else str(pages)
                doc_type = getattr(pages, "document_type", "digital_pdf")
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
                    doc_type = getattr(pages, "document_type", "digital_pdf")
                    text = pages.to_text() if hasattr(pages, "to_text") else str(pages)
                    quality = assess_readability(text)
                    _breadcrumb("pdf.extract.done", {"chars": len(text), "pages": len(pages), "doc_type": doc_type, "readable": quality["readable"]})
                    print(f"[worker] Extracted {len(pages)} pages from '{filename}' | document_type={doc_type} | readable={quality['readable']}")

                    has_unclear_or_scanned = not quality["readable"] or doc_type in ("scanned_pdf", "mixed_pdf")
                    if has_unclear_or_scanned:
                        can_visual = ocr_available() or (settings.cloud_vision_enabled and not settings.privacy_mode and bool(settings.gemini_api_key))
                        if can_visual:
                            print(f"[worker] Running Visual / OCR Pipeline on '{filename}' (doc_type={doc_type})…")
                            await _update_job_stage(db, document_id, "ocr", 40)
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
                            _ocr_done_at = datetime.utcnow().isoformat()
                            await _upsert_analysis(
                                db, analysis_id, document_id,
                                json.dumps({"status": "processing", "started_at": _ocr_done_at}),
                                _ocr_done_at,
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
                    print(f"[worker] Image document '{filename}' → running Visual / OCR Pipeline…")
                    await _update_job_stage(db, document_id, "ocr", 40)
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
                    _ocr_done_at = datetime.utcnow().isoformat()
                    await _upsert_analysis(
                        db, analysis_id, document_id,
                        json.dumps({"status": "processing", "started_at": _ocr_done_at}),
                        _ocr_done_at,
                    )

            if not text or not quality.get("readable", False):
                raise ValueError(
                    "No sufficiently readable text could be extracted from this document. "
                    "If it is scanned, enable OCR; otherwise upload a valid text-based PDF or a clearer image."
                )

            print(f"[worker] Extracted {len(text)} chars from '{filename}' | script={quality.get('script')}")

            # Cache extracted text so chat doesn't re-parse the PDF
            await set_doc_text(document_id, text, ttl=settings.redis_cache_ttl)

            # ── Step 2: AI analysis ───────────────────────────────────────────
            await _update_job_stage(db, document_id, "analyzing", 60)
            _breadcrumb("ai.analyze.start", {"filename": filename})
            analysis = await asyncio.wait_for(
                analyze_legal_document(text, filename),
                timeout=settings.analysis_timeout_seconds,
            )
            analysis = validate_analysis(analysis)

            # ── Step 2b: Enrich verified legal citations (SL-028 & SL-029) ─────
            if "clauses" in analysis and isinstance(analysis["clauses"], list):
                analysis["clauses"] = enrich_clause_citations(analysis["clauses"])

            # ── Step 2c: Attach version & optimization metadata (Phase 6) ─────
            meta = analysis.setdefault("metadata", {})
            meta["pipeline_version"] = "v1.0.0"
            meta["prompt_version"] = PROMPT_VERSION
            meta["model"] = settings.groq_model
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

            # ── Step 3: Persist ───────────────────────────────────────────────
            await _upsert_analysis(db, analysis_id, document_id, json.dumps(analysis), analysis["analyzed_at"])
            doc_type = analysis.get("summary", {}).get("document_type", "")
            await db.execute(
                "UPDATE documents SET document_type = $1 WHERE id = $2",
                doc_type, document_id,
            )

            # Mark job stage completed (100%)
            await _update_job_stage(db, document_id, "completed", 100)

            # ── Step 4: Write to Redis L1 cache ───────────────────────────────
            await set_analysis(document_id, analysis, ttl=settings.redis_cache_ttl)

            print(f"[worker] Done — document_id={document_id}")

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
                    "stage": "worker_analysis",
                },
            )
            print(f"[worker] FAILED {document_id}: {message}")
            await _update_job_stage(db, document_id, "failed", 0, error_message=message)
            error_payload = json.dumps(
                {"status": "error", "error": message, "document_id": document_id}
            )
            await _upsert_analysis(db, analysis_id, document_id, error_payload, datetime.utcnow().isoformat())

        finally:
            # Deterministic derived artifact cleanup on both success and failure (Phase 6)
            if os.path.exists(scratch_dir):
                try:
                    shutil.rmtree(scratch_dir, ignore_errors=True)
                except Exception:
                    pass



# ── ARQ job function ──────────────────────────────────────────────────────────

async def run_analysis_job(ctx: dict, document_id: str, file_bytes: bytes, filename: str) -> dict:
    """
    ARQ job entry point.
    `ctx` is injected by ARQ and contains the Redis pool.
    Returns a summary dict that ARQ stores as the job result.
    """
    print(f"[arq-worker] Starting analysis for document_id={document_id} filename={filename!r}")
    await _execute_analysis(document_id, file_bytes, filename)
    return {"document_id": document_id, "status": "done"}


# ── ARQ startup / shutdown hooks ──────────────────────────────────────────────

async def startup(ctx: dict) -> None:
    """Called once when the ARQ worker process starts."""
    from database import init_db_pool
    from cache import init_redis
    await init_db_pool()
    await init_redis(settings.redis_url)
    print("[arq-worker] Startup complete — DB pool and Redis initialised.")


async def shutdown(ctx: dict) -> None:
    """Called once when the ARQ worker process stops."""
    from database import close_db_pool
    from cache import close_redis
    await close_db_pool()
    await close_redis()
    print("[arq-worker] Shutdown complete.")


# ── WorkerSettings class consumed by `arq worker worker.WorkerSettings` ───────

class WorkerSettings:
    functions = [run_analysis_job]
    on_startup = startup
    on_shutdown = shutdown
    # How long a job can run before ARQ cancels it and retries (or marks failed).
    job_timeout = settings.analysis_timeout_seconds
    # Retry stale/failed jobs up to 2 additional times.
    max_tries = 3
    # Queue name — must match what enqueue_analysis uses.
    queue_name = "smartlegal:analysis"
    # Health-check interval for the worker loop.
    health_check_interval = 30


# ── Enqueue helper used by the HTTP router ────────────────────────────────────

async def enqueue_analysis(document_id: str, file_bytes: bytes, filename: str) -> str:
    """
    Enqueue an analysis job via ARQ when Redis is available.
    Falls back to a direct asyncio call when Redis is not configured,
    preserving development-mode behaviour without Redis.

    Returns the job_id (or "direct" for the fallback path).
    """
    if not settings.redis_url:
        # Dev fallback: run inline (same as old BackgroundTasks behaviour)
        asyncio.create_task(_execute_analysis(document_id, file_bytes, filename))
        return "direct"

    from arq import create_pool
    from arq.connections import RedisSettings

    redis_pool = await create_pool(
        RedisSettings.from_dsn(settings.redis_url),
        default_queue_name=WorkerSettings.queue_name,
    )
    # Use document_id as job_id for natural deduplication: a second POST
    # for the same document while already queued just returns the existing job.
    job = await redis_pool.enqueue_job(
        "run_analysis_job",
        document_id,
        file_bytes,
        filename,
        _job_id=f"analysis:{document_id}",
        _queue_name=WorkerSettings.queue_name,
    )
    await redis_pool.close()
    return job.job_id if job else f"analysis:{document_id}"