"""
cache.py — async Redis cache layer for analysis results.

Design decisions:
- Redis is OPTIONAL. If REDIS_URL is blank the app works exactly as before
  (PostgreSQL is the only store). No KeyError, no crash on startup.
- One module-level client is created once and reused across all requests
  (connection pooling is built into redis-py).
- Cache key:  "analysis:{document_id}"
- TTL:        REDIS_CACHE_TTL seconds (default 24 h), refreshed on every write.
- On any Redis error we log the exception, capture it to Sentry if configured,
  and let the caller fall through to the DB — Redis is a speed layer, not a
  source of truth.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Module-level client — None when Redis is not configured.
_redis: Any = None


async def init_redis(redis_url: str) -> None:
    """
    Call once during app startup (lifespan) when REDIS_URL is set.
    Creates a single async connection pool shared across the process.
    """
    global _redis
    if not redis_url:
        logger.info("[cache] REDIS_URL not set — Redis cache disabled.")
        return
    try:
        from redis.asyncio import from_url
        _redis = await from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,   # fail fast on misconfigured URL
            socket_timeout=3,
        )
        # Ping to confirm the connection works at startup
        await _redis.ping()
        logger.info("[cache] Redis connected: %s", redis_url.split("@")[-1])
    except Exception as exc:
        logger.warning("[cache] Redis init failed — cache disabled: %s", exc)
        _redis = None


async def close_redis() -> None:
    """Call on app shutdown to cleanly close the connection pool."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Public API ────────────────────────────────────────────────────────────────

def _key(document_id: str) -> str:
    return f"analysis:{document_id}"


def _capture_silent(exc: Exception, context: dict) -> None:
    """Forward Redis errors to Sentry without raising."""
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("layer", "redis_cache")
            for k, v in context.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except ImportError:
        pass


async def get_analysis(document_id: str) -> dict | None:
    """
    Return the cached analysis dict for document_id, or None on miss / error.
    Never raises — Redis failures are swallowed and logged.
    """
    if _redis is None:
        return None
    try:
        raw = await _redis.get(_key(document_id))
        if raw is None:
            return None
        result = json.loads(raw)
        logger.debug("[cache] HIT  document_id=%s", document_id)
        return result
    except Exception as exc:
        logger.warning("[cache] GET failed for %s: %s", document_id, exc)
        _capture_silent(exc, {"document_id": document_id, "op": "get"})
        return None


async def set_analysis(document_id: str, data: dict, ttl: int) -> None:
    """
    Store an analysis result in Redis with the given TTL (seconds).
    Never raises — Redis failures are swallowed and logged.
    """
    if _redis is None:
        return
    try:
        await _redis.set(_key(document_id), json.dumps(data), ex=ttl)
        logger.debug("[cache] SET  document_id=%s  ttl=%ds", document_id, ttl)
    except Exception as exc:
        logger.warning("[cache] SET failed for %s: %s", document_id, exc)
        _capture_silent(exc, {"document_id": document_id, "op": "set"})


async def delete_analysis(document_id: str) -> None:
    """
    Evict a cached entry — call when force_reanalyze=True or cache is cleared.
    Never raises.
    """
    if _redis is None:
        return
    try:
        await _redis.delete(_key(document_id))
        logger.debug("[cache] DEL  document_id=%s", document_id)
    except Exception as exc:
        logger.warning("[cache] DEL failed for %s: %s", document_id, exc)
        _capture_silent(exc, {"document_id": document_id, "op": "delete"})