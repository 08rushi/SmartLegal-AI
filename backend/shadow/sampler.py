"""
sampler.py — Deterministic Traffic Sampler & Multi-Gate Eligibility Inspector (Phase 9).
Provides cryptographically uniform, salted SHA-256 bucket allocation and multi-stage eligibility checks.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional, Tuple

from config import get_settings
from shadow.config import ShadowSettings, get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")


def calculate_sampling_bucket(document_id: str, salt: str) -> int:
    """
    Computes a deterministic integer bucket between 0 and 9999 (0.01% resolution).
    Uses SHA-256 for uniform cryptographic distribution and collision resistance.
    """
    input_str = f"{document_id}:{salt}".encode("utf-8")
    hash_digest = hashlib.sha256(input_str).hexdigest()
    # First 8 hex characters = 32-bit unsigned integer
    return int(hash_digest[:8], 16) % 10000


def is_sample_selected(document_id: str, sample_rate_pct: float, salt: str) -> bool:
    """
    Evaluates whether document_id falls within the deterministic percentage threshold.
    Guarantees stable, reproducible sampling across application lifecycles.
    """
    if sample_rate_pct <= 0.0:
        return False
    if sample_rate_pct >= 100.0:
        return True
    threshold = int(sample_rate_pct * 100)  # e.g., 5.0% -> 500
    return calculate_sampling_bucket(document_id, salt) < threshold


async def check_shadow_eligibility(
    document_id: str,
    file_bytes: bytes,
    filename: str,
    shadow_settings: Optional[ShadowSettings] = None,
) -> Tuple[bool, str]:
    """
    Multi-gate inspector verifying all prerequisites for shadow execution:
    1. Master feature switch
    2. Emergency kill switch
    3. Global privacy mode
    4. Payload size limits (15 MB ceiling)
    5. Daily budget ceiling
    6. Deterministic sampling hash
    """
    settings = shadow_settings or get_shadow_settings()
    app_settings = get_settings()

    # Gate 1: Master Feature Switch
    if not settings.shadow_mode_enabled:
        return False, "shadow_mode_disabled"

    # Gate 2: Privacy Mode
    if getattr(app_settings, "privacy_mode", False):
        return False, "privacy_mode_enabled"

    # Gate 3: Emergency Kill Switch (Redis or local)
    try:
        from shadow.circuit_breaker import is_kill_switch_active
        if await is_kill_switch_active(settings.shadow_experiment_id):
            return False, "kill_switch_active"
    except Exception as exc:
        logger.warning("[SHADOW] Kill switch check encountered exception: %s", exc)

    # Gate 4: Financial Budget Ceiling
    try:
        from shadow.budget import get_shadow_budget_manager
        budget_mgr = get_shadow_budget_manager()
        is_allowed, reason = await budget_mgr.is_request_allowed(
            estimated_tokens=settings.shadow_max_prompt_tokens
        )
        if not is_allowed:
            return False, f"budget_denied_{reason}"
    except Exception as exc:
        logger.warning("[SHADOW] Budget check encountered exception: %s", exc)

    # Gate 5: Payload Resource Ceiling (Max 15 MB)
    max_shadow_bytes = 15 * 1024 * 1024
    if len(file_bytes) > max_shadow_bytes:
        return False, "payload_exceeds_shadow_limit"

    # Gate 6: Deterministic Traffic Sampling
    # Check dynamic Redis sampling rate override if present
    sampling_pct = settings.shadow_traffic_percentage
    try:
        from shadow.circuit_breaker import get_dynamic_shadow_percentage
        dynamic_pct = await get_dynamic_shadow_percentage()
        if dynamic_pct is not None:
            sampling_pct = dynamic_pct
    except Exception:
        pass

    if not is_sample_selected(document_id, sampling_pct, settings.shadow_traffic_salt):
        return False, "not_sampled"

    return True, "eligible"


async def maybe_enqueue_shadow_analysis(
    document_id: str,
    file_bytes: bytes,
    filename: str,
    user_id: str,
) -> bool:
    """
    Non-blocking hook invoked by the primary analysis router.
    Evaluates eligibility and enqueues to the dedicated shadow worker.
    Guarantees absolute exception isolation — will NEVER raise.
    """
    try:
        eligible, reason = await check_shadow_eligibility(document_id, file_bytes, filename)
        if not eligible:
            logger.debug("[SHADOW] Document %s ineligible for shadow: %s", document_id, reason)
            return False

        from shadow.worker import enqueue_shadow_job
        job_id = await enqueue_shadow_job(
            document_id=document_id,
            file_bytes=file_bytes,
            filename=filename,
            user_id=user_id,
        )
        logger.info(
            "[SHADOW] Document %s enqueued for shadow execution (job_id=%s)",
            document_id,
            job_id,
        )
        return True
    except Exception as exc:
        # Non-negotiable safety invariant: Shadow failures must never affect primary execution
        logger.warning("[SHADOW] Failed to enqueue shadow job for %s: %s", document_id, exc)
        return False


async def should_serve_canary(document_id: str) -> bool:
    """
    Evaluates whether live traffic should be routed to candidate model under Canary mode.
    Guarantees that when Canary is disabled or kill switch is active, returns False.
    """
    settings = get_shadow_settings()
    if not settings.canary_mode_enabled:
        return False

    try:
        from shadow.circuit_breaker import is_kill_switch_active, get_dynamic_canary_percentage
        if await is_kill_switch_active(settings.shadow_experiment_id):
            return False

        canary_pct = settings.canary_traffic_percentage
        dynamic_pct = await get_dynamic_canary_percentage()
        if dynamic_pct is not None:
            canary_pct = dynamic_pct

        if canary_pct <= 0.0:
            return False

        return is_sample_selected(document_id, canary_pct, settings.canary_traffic_salt)
    except Exception as exc:
        logger.warning("[CANARY-ROUTER] Canary check error for %s: %s", document_id, exc)
        return False

