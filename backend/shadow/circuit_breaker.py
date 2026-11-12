"""
circuit_breaker.py — Multi-Tier Kill Switch & Automated Rollback Engine (Phase 9).
Provides sub-500ms emergency stops and autonomous anomaly-based canary rollbacks.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Tuple

from shadow.config import get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")

# In-memory fallbacks when Redis is unconfigured
_in_memory_switches: dict[str, str] = {}
_in_memory_metrics: dict[str, list[dict]] = {}


async def _get_redis():
    try:
        import cache
        return cache._redis
    except Exception:
        return None


# ── Multi-Tier Emergency Kill Switch ──────────────────────────────────────────

async def is_kill_switch_active(experiment_id: str = "") -> bool:
    """
    Checks both global kill switch and experiment-specific kill switch.
    Returns True if either switch is active ('1' or 'true').
    """
    r = await _get_redis()
    global_key = "shadow:global_kill_switch"
    exp_key = f"shadow:kill_switch:{experiment_id}" if experiment_id else ""

    if r is not None:
        try:
            if await r.get(global_key) in ("1", "true"):
                return True
            if exp_key and await r.get(exp_key) in ("1", "true"):
                return True
            return False
        except Exception as exc:
            logger.warning("[SHADOW-KILLSWITCH] Redis read failed: %s", exc)

    if _in_memory_switches.get(global_key) in ("1", "true"):
        return True
    if exp_key and _in_memory_switches.get(exp_key) in ("1", "true"):
        return True

    return False


async def set_kill_switch(experiment_id: Optional[str] = None, active: bool = True) -> None:
    """
    Activates or deactivates emergency stop.
    If experiment_id is None, flips the global kill switch.
    Propagates in under 500ms across distributed workers.
    """
    val = "1" if active else "0"
    target_key = f"shadow:kill_switch:{experiment_id}" if experiment_id else "shadow:global_kill_switch"
    r = await _get_redis()

    if r is not None:
        try:
            await r.set(target_key, val)
            logger.warning("[SHADOW-KILLSWITCH] Set %s = %s in Redis", target_key, val)
        except Exception as exc:
            logger.error("[SHADOW-KILLSWITCH] Failed to set %s in Redis: %s", target_key, exc)

    _in_memory_switches[target_key] = val
    logger.info("[SHADOW-KILLSWITCH] Local state updated: %s = %s", target_key, val)


# ── Dynamic Traffic Percentages Overrides ──────────────────────────────────────

async def get_dynamic_shadow_percentage() -> Optional[float]:
    r = await _get_redis()
    key = "shadow:dynamic_traffic_percentage"
    if r is not None:
        try:
            val = await r.get(key)
            if val is not None:
                return float(val)
        except Exception:
            pass
    if key in _in_memory_switches:
        return float(_in_memory_switches[key])
    return None


async def set_dynamic_shadow_percentage(percentage: float) -> None:
    clamped = max(0.0, min(100.0, float(percentage)))
    key = "shadow:dynamic_traffic_percentage"
    r = await _get_redis()
    if r is not None:
        try:
            await r.set(key, str(clamped))
        except Exception:
            pass
    _in_memory_switches[key] = str(clamped)


async def get_dynamic_canary_percentage() -> Optional[float]:
    r = await _get_redis()
    key = "shadow:canary_traffic_percentage"
    if r is not None:
        try:
            val = await r.get(key)
            if val is not None:
                return float(val)
        except Exception:
            pass
    if key in _in_memory_switches:
        return float(_in_memory_switches[key])
    return None


async def set_dynamic_canary_percentage(percentage: float) -> None:
    clamped = max(0.0, min(100.0, float(percentage)))
    key = "shadow:canary_traffic_percentage"
    r = await _get_redis()
    if r is not None:
        try:
            await r.set(key, str(clamped))
        except Exception:
            pass
    _in_memory_switches[key] = str(clamped)


# ── Automated Rollback Circuit Breaker Engine ─────────────────────────────────

async def record_execution_metric(
    experiment_id: str,
    success: bool,
    latency_ms: int,
    is_schema_error: bool = False,
) -> None:
    """Records health data in sliding window to detect anomalies."""
    metric = {
        "success": success,
        "latency_ms": latency_ms,
        "is_schema_error": is_schema_error,
    }
    history = _in_memory_metrics.setdefault(experiment_id, [])
    history.append(metric)
    if len(history) > 50:
        history.pop(0)


async def evaluate_circuit_breakers(experiment_id: str) -> Tuple[bool, str]:
    """
    Evaluates rolling metrics against safety thresholds:
    1. Error rate > 3.0% over recent calls -> Automated Rollback to 0% canary
    2. Consecutive schema errors >= limit -> Automated Rollback to 0% canary
    Returns (tripped: bool, reason: str).
    """
    settings = get_shadow_settings()
    history = _in_memory_metrics.get(experiment_id, [])

    if len(history) >= 10:
        failures = sum(1 for m in history if not m["success"])
        error_rate_pct = (failures / len(history)) * 100.0

        if error_rate_pct > settings.shadow_error_rate_threshold_pct:
            reason = f"Error rate spike: {error_rate_pct:.1f}% exceeds threshold {settings.shadow_error_rate_threshold_pct}%"
            # Automatically roll back canary to 0%
            await set_dynamic_canary_percentage(0.0)
            logger.error("[SHADOW-ROLLBACK] CIRCUIT BREAKER TRIPPED: %s. Resetting canary to 0%%.", reason)
            return True, reason

    # Check consecutive schema errors
    consecutive_schema_errors = 0
    for m in reversed(history):
        if m.get("is_schema_error"):
            consecutive_schema_errors += 1
        else:
            break

    if consecutive_schema_errors >= settings.shadow_consecutive_schema_errors_limit:
        reason = f"Consecutive schema violations: {consecutive_schema_errors} >= {settings.shadow_consecutive_schema_errors_limit}"
        await set_dynamic_canary_percentage(0.0)
        logger.error("[SHADOW-ROLLBACK] CIRCUIT BREAKER TRIPPED: %s. Resetting canary to 0%%.", reason)
        return True, reason

    return False, "healthy"
