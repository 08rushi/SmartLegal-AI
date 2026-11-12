"""
worker.py — Dedicated ARQ Shadow Analysis Worker (Phase 9).
Processes candidate model evaluation jobs on an isolated queue ('smartlegal:shadow_analysis')
with strict concurrency capping (<= 2) and 300s timeouts.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import uuid
from typing import Optional

from config import get_settings
from database import get_db_ctx
from shadow.circuit_breaker import (
    evaluate_circuit_breakers,
    is_kill_switch_active,
    record_execution_metric,
)
from shadow.comparison import ShadowComparisonAdapter
from shadow.config import FailureCategory, get_shadow_settings
from shadow.service import ShadowAnalysisService

logger = logging.getLogger("smartlegal.shadow")


async def run_shadow_analysis_job(
    ctx: Optional[dict],
    document_id: str,
    file_bytes: bytes,
    filename: str,
    user_id: str,
) -> None:
    """
    Executes a single candidate model analysis job.
    Completely isolated from primary production analysis.
    """
    settings = get_shadow_settings()
    experiment_id = settings.shadow_experiment_id

    # Pre-execution check: Emergency Kill Switch
    if await is_kill_switch_active(experiment_id):
        logger.warning(
            "[SHADOW-WORKER] Job cancelled for document %s: Kill switch active",
            document_id,
        )
        return

    # 1. Retrieve or extract document text
    # Optimisation: Check if primary pipeline already cached the extracted text
    text: Optional[str] = None
    try:
        from cache import get_doc_text
        text = await get_doc_text(document_id)
    except Exception as exc:
        logger.debug("[SHADOW-WORKER] Redis text cache lookup missed: %s", exc)

    if not text:
        try:
            from services.pdf_parser import extract_text_from_pdf
            pages, _ = extract_text_from_pdf(file_bytes)
            text = "\n\n".join(pages) if isinstance(pages, list) else str(pages or "")
        except Exception as exc:
            logger.warning("[SHADOW-WORKER] Text extraction failed for %s: %s", document_id, exc)
            text = ""

    if not text.strip():
        logger.warning("[SHADOW-WORKER] Empty text for document %s, skipping shadow run", document_id)
        return

    # 2. Execute candidate analysis service
    service = ShadowAnalysisService()
    exec_result = await service.execute_candidate_analysis(text, document_id)

    # 3. Telemetry and circuit breaker accounting
    is_schema_err = exec_result.failure_category == FailureCategory.SHADOW_INVALID_OUTPUT
    await record_execution_metric(
        experiment_id=experiment_id,
        success=exec_result.success,
        latency_ms=exec_result.latency_ms,
        is_schema_error=is_schema_err,
    )
    await evaluate_circuit_breakers(experiment_id)

    # 4. Persist to shadow_analyses table
    shadow_analysis_id = str(uuid.uuid4())
    status_str = "success" if exec_result.success else "failed"
    failure_code = exec_result.failure_category.value if exec_result.failure_category else None

    async with get_db_ctx() as db:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.execute(
            """INSERT INTO shadow_analyses (
                id, experiment_id, document_id, candidate_provider,
                candidate_model, candidate_version, source_document_hash,
                result_json, execution_status, failure_category,
                prompt_tokens, completion_tokens, estimated_cost_usd,
                started_at, completed_at, latency_ms, rollout_stage, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
            )
            ON CONFLICT (experiment_id, document_id)
            DO UPDATE SET
                result_json = EXCLUDED.result_json,
                execution_status = EXCLUDED.execution_status,
                failure_category = EXCLUDED.failure_category,
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                estimated_cost_usd = EXCLUDED.estimated_cost_usd,
                completed_at = EXCLUDED.completed_at,
                latency_ms = EXCLUDED.latency_ms,
                created_at = EXCLUDED.created_at""",
            shadow_analysis_id,
            experiment_id,
            document_id,
            settings.shadow_candidate_provider,
            settings.shadow_candidate_model,
            "v1.0",
            exec_result.source_hash,
            json.dumps(exec_result.result_data),
            status_str,
            failure_code,
            exec_result.prompt_tokens,
            exec_result.completion_tokens,
            exec_result.estimated_cost_usd,
            exec_result.started_at,
            exec_result.completed_at,
            exec_result.latency_ms,
            "shadow",
            now_str,
        )

    logger.info(
        "[SHADOW-WORKER] Completed candidate analysis for %s (status=%s, latency=%dms)",
        document_id,
        status_str,
        exec_result.latency_ms,
    )

    # 5. Offline Accuracy Evaluation Adapter: Compare against primary analysis if ready
    if exec_result.success:
        try:
            async with get_db_ctx() as db:
                row = await db.fetchrow(
                    "SELECT id, result_json FROM analyses WHERE document_id = $1",
                    document_id,
                )
                if row and row["result_json"]:
                    primary_data = json.loads(row["result_json"])
                    if primary_data.get("status") == "done":
                        await ShadowComparisonAdapter.compare_and_persist(
                            experiment_id=experiment_id,
                            document_id=document_id,
                            primary_data=primary_data,
                            shadow_data=exec_result.result_data,
                            shadow_analysis_id=shadow_analysis_id,
                            shadow_latency_ms=exec_result.latency_ms,
                            shadow_tokens=exec_result.prompt_tokens + exec_result.completion_tokens,
                            shadow_cost_usd=exec_result.estimated_cost_usd,
                        )
        except Exception as exc:
            logger.warning("[SHADOW-WORKER] Comparative adapter error for %s: %s", document_id, exc)


class ShadowWorkerSettings:
    """ARQ settings for the dedicated shadow queue worker."""
    functions = [run_shadow_analysis_job]
    queue_name = get_shadow_settings().shadow_queue_name
    job_timeout = get_shadow_settings().shadow_job_timeout_seconds
    max_tries = 1  # Never retry candidate failures
    max_jobs = get_shadow_settings().shadow_max_concurrency


async def enqueue_shadow_job(
    document_id: str,
    file_bytes: bytes,
    filename: str,
    user_id: str,
) -> str:
    """
    Submits a candidate evaluation job to the dedicated shadow queue.
    Falls back to inline asyncio task if Redis is unconfigured.
    """
    app_settings = get_settings()
    shadow_settings = get_shadow_settings()
    exp_id = shadow_settings.shadow_experiment_id

    if not app_settings.redis_url:
        # Development / test mode fallback
        asyncio.create_task(
            run_shadow_analysis_job(None, document_id, file_bytes, filename, user_id)
        )
        return "direct_shadow"

    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis_pool = await create_pool(
            RedisSettings.from_dsn(app_settings.redis_url),
            default_queue_name=shadow_settings.shadow_queue_name,
        )
        job = await redis_pool.enqueue_job(
            "run_shadow_analysis_job",
            document_id,
            file_bytes,
            filename,
            user_id,
            _job_id=f"shadow:{exp_id}:{document_id}",
            _queue_name=shadow_settings.shadow_queue_name,
        )
        await redis_pool.close()
        return job.job_id if job else f"shadow:{exp_id}:{document_id}"
    except Exception as exc:
        logger.warning("[SHADOW-WORKER] ARQ shadow enqueue failed, falling back to task: %s", exc)
        asyncio.create_task(
            run_shadow_analysis_job(None, document_id, file_bytes, filename, user_id)
        )
        return "fallback_shadow"
