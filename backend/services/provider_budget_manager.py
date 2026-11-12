"""
provider_budget_manager.py — Provider Budget & Rate-Limit Tracking (Phase 1 & Phase 5).

Defines the ProviderBudgetManager interface and production implementation with:
- Token-budget enforcement (TPM / RPM rolling windows)
- Actual request / token accounting
- Defensive rate-limit HTTP header parsing
- Redis-backed distributed cooldown tracking with in-memory fallback
- Provider status & queued states
"""

from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from config import get_settings
from services.model_capabilities import ModelCapability

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate-Limit Header & Duration Parsing (Phase 5)
# ---------------------------------------------------------------------------

_DURATION_UNITS = {
    "d": 86400.0,
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
    "us": 0.000001,
    "µs": 0.000001,
}

_DURATION_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*(d|h|ms|us|µs|m|s)")


def parse_duration_string(val: Union[str, int, float, None]) -> Optional[float]:
    """
    Defensively parse duration from numbers, strings with units, or timestamps.
    Returns duration in seconds (float), or None if unparseable.
    Never raises an exception.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        num = float(val)
        if num > 1_000_000_000:
            if num > 100_000_000_000:
                num = num / 1000.0
            diff = num - time.time()
            return max(0.0, float(diff))
        return max(0.0, num)

    val_str = str(val).strip()
    if not val_str:
        return None

    # Try direct numeric
    try:
        num = float(val_str)
        # Check if it's an epoch timestamp (> 1 billion seconds or milliseconds)
        if num > 1_000_000_000:
            if num > 100_000_000_000:
                num = num / 1000.0
            diff = num - time.time()
            return max(0.0, float(diff))
        return max(0.0, num)
    except ValueError:
        pass

    # Try regex units (e.g. "2s", "60ms", "1m30s")
    matches = _DURATION_REGEX.findall(val_str.lower())
    if matches:
        total = 0.0
        for amount, unit in matches:
            total += float(amount) * _DURATION_UNITS.get(unit, 1.0)
        return total

    # Try HTTP date format
    try:
        dt = parsedate_to_datetime(val_str)
        diff = dt.timestamp() - time.time()
        return max(0.0, float(diff))
    except Exception:
        pass

    return None


def parse_rate_limit_headers(headers: Any) -> Dict[str, Any]:
    """
    Defensively parse provider rate-limit headers (Groq, OpenRouter, etc.).
    Extracts remaining tokens, remaining requests, reset durations, and retry-after.
    Case-insensitive, safe against missing or malformed inputs.
    """
    result: Dict[str, Any] = {
        "remaining_tokens": None,
        "remaining_requests": None,
        "reset_tokens": None,
        "reset_requests": None,
        "retry_after": None,
    }
    if not headers:
        return result

    try:
        if hasattr(headers, "items"):
            h_dict = {str(k).lower(): str(v) for k, v in headers.items()}
        else:
            h_dict = {str(k).lower(): str(v) for k, v in dict(headers).items()}
    except Exception as exc:
        logger.debug("[budget-manager] Could not convert headers to dict: %s", exc)
        return result

    # 1. Remaining tokens
    for key in (
        "x-ratelimit-remaining-tokens",
        "ratelimit-remaining-tokens",
        "x-ratelimit-remaining-tokens-minute",
        "x-ratelimit-remaining-tokens-day",
    ):
        if key in h_dict:
            try:
                result["remaining_tokens"] = int(float(h_dict[key]))
                break
            except (ValueError, TypeError):
                pass

    # 2. Remaining requests
    for key in (
        "x-ratelimit-remaining-requests",
        "ratelimit-remaining-requests",
        "x-ratelimit-remaining-requests-minute",
        "x-ratelimit-remaining-requests-day",
    ):
        if key in h_dict:
            try:
                result["remaining_requests"] = int(float(h_dict[key]))
                break
            except (ValueError, TypeError):
                pass

    # 3. Reset tokens
    for key in (
        "x-ratelimit-reset-tokens",
        "ratelimit-reset-tokens",
        "x-ratelimit-reset-tokens-minute",
    ):
        if key in h_dict:
            dur = parse_duration_string(h_dict[key])
            if dur is not None:
                result["reset_tokens"] = dur
                break

    # 4. Reset requests
    for key in (
        "x-ratelimit-reset-requests",
        "ratelimit-reset-requests",
        "x-ratelimit-reset-requests-minute",
        "x-ratelimit-reset",
    ):
        if key in h_dict:
            dur = parse_duration_string(h_dict[key])
            if dur is not None:
                result["reset_requests"] = dur
                break

    # 5. Retry-After
    for key in ("retry-after", "retry-after-ms"):
        if key in h_dict:
            dur = parse_duration_string(h_dict[key])
            if dur is not None:
                if key == "retry-after-ms":
                    dur = dur / 1000.0
                result["retry_after"] = dur
                break

    # Derive retry_after if missing but tokens/requests exhausted and reset known
    if result["retry_after"] is None:
        if result["remaining_tokens"] is not None and result["remaining_tokens"] <= 0 and result["reset_tokens"]:
            result["retry_after"] = result["reset_tokens"]
        elif result["remaining_requests"] is not None and result["remaining_requests"] <= 0 and result["reset_requests"]:
            result["retry_after"] = result["reset_requests"]

    return result


# ---------------------------------------------------------------------------
# Abstract interface  (Section D — approved architecture)
# ---------------------------------------------------------------------------

class ProviderBudgetManager(ABC):
    """
    Abstract interface for per-provider budget / availability tracking.

    Phase 1 & Phase 5 shared interface:
        can_send(request_tokens, capability)   -> bool
        record_success(provider, model, tokens_used)
        record_rate_limit(provider, retry_after)
    """

    @abstractmethod
    async def can_send(
        self,
        request_tokens: int,
        capability: ModelCapability,
    ) -> bool:
        """
        Return True if capability.provider can currently accept a request
        of size request_tokens.
        """

    @abstractmethod
    async def record_success(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        """Record a successful API call and update token accounting."""

    @abstractmethod
    async def record_rate_limit(
        self,
        provider: str,
        retry_after: int,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        """Record that provider returned a rate-limit response."""


# ---------------------------------------------------------------------------
# In-memory implementation (Phase 1 Baseline)
# ---------------------------------------------------------------------------

@dataclass
class _ProviderState:
    """Mutable per-provider counters and availability flag."""
    success_count: int = 0
    rate_limit_count: int = 0
    total_tokens_used: int = 0
    # True while the provider is considered rate-limited / unavailable.
    rate_limited: bool = False
    # Wall-clock time (seconds, monotonic) when the last rate-limit was recorded.
    rate_limited_since: float = field(default=0.0)
    # How long (seconds) this particular cooloff should last.
    current_cooloff: float = field(default=0.0)


class InMemoryProviderBudgetManager(ProviderBudgetManager):
    """
    Minimal in-memory ProviderBudgetManager — Phase 1 base implementation.
    Preserved for 100% Phase 1 backward compatibility.
    """

    def __init__(self, default_cooloff_seconds: float = 60.0) -> None:
        self._default_cooloff: float = default_cooloff_seconds
        self._states: Dict[str, _ProviderState] = {}

    def _get_state(self, provider: str) -> _ProviderState:
        if provider not in self._states:
            self._states[provider] = _ProviderState()
        return self._states[provider]

    def _check_cooloff(self, state: _ProviderState) -> None:
        """Clear rate-limit flag once the cooloff period has elapsed."""
        if state.rate_limited:
            elapsed = time.monotonic() - state.rate_limited_since
            if elapsed >= state.current_cooloff:
                logger.info(
                    "[budget-manager] Cooloff elapsed (%.0f s). Provider available again.",
                    elapsed,
                )
                state.rate_limited = False

    async def can_send(
        self,
        request_tokens: int,
        capability: ModelCapability,
    ) -> bool:
        state = self._get_state(capability.provider)
        self._check_cooloff(state)
        available = not state.rate_limited
        if not available:
            logger.debug(
                "[budget-manager] Provider %r is rate-limited; blocking request "
                "(requested %d tokens for model %r).",
                capability.provider,
                request_tokens,
                capability.name,
            )
        return available

    async def record_success(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        state = self._get_state(provider)
        state.success_count += 1
        state.total_tokens_used += tokens_used
        state.rate_limited = False

    async def record_rate_limit(
        self,
        provider: str,
        retry_after: int,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        state = self._get_state(provider)
        state.rate_limit_count += 1
        state.rate_limited = True
        state.rate_limited_since = time.monotonic()
        state.current_cooloff = float(retry_after) if retry_after > 0 else self._default_cooloff

    def reset(self, provider: str) -> None:
        """Clear all state for provider."""
        self._states.pop(provider, None)

    def get_stats(self, provider: str) -> dict:
        """Return a snapshot of counters/state for provider."""
        state = self._get_state(provider)
        self._check_cooloff(state)
        return {
            "provider": provider,
            "available": not state.rate_limited,
            "success_count": state.success_count,
            "rate_limit_count": state.rate_limit_count,
            "total_tokens_used": state.total_tokens_used,
            "rate_limited": state.rate_limited,
            "rate_limited_since": state.rate_limited_since,
            "current_cooloff": state.current_cooloff,
            "default_cooloff_seconds": self._default_cooloff,
        }


# ---------------------------------------------------------------------------
# Production Implementation (Phase 5)
# ---------------------------------------------------------------------------

class ProductionProviderBudgetManager(InMemoryProviderBudgetManager):
    """
    Production ProviderBudgetManager supporting:
    - Sliding window token & request quota tracking (TPM / RPM)
    - Defensive header parsing & remaining-token awareness
    - Redis-backed distributed cooldown tracking with in-memory fallback
    - Rich provider status and queued state introspection
    """

    def __init__(
        self,
        default_cooloff_seconds: float | None = None,
        redis_client: Any = None,
    ) -> None:
        settings = get_settings()
        cooloff = (
            default_cooloff_seconds
            if default_cooloff_seconds is not None
            else getattr(settings, "provider_cooldown_seconds", 60.0)
        )
        super().__init__(default_cooloff_seconds=cooloff)
        self._redis_client = redis_client
        self._token_windows: Dict[str, List[Tuple[float, int]]] = {}
        self._request_windows: Dict[str, List[float]] = {}
        self._header_states: Dict[str, Dict[str, Any]] = {}

    def _get_redis(self) -> Any:
        if self._redis_client is not None:
            return self._redis_client
        try:
            import cache
            return getattr(cache, "_redis", None)
        except ImportError:
            return None

    def _clean_windows(self, provider: str, now: float) -> None:
        window_start = now - 60.0
        if provider in self._token_windows:
            self._token_windows[provider] = [
                (ts, tokens) for ts, tokens in self._token_windows[provider] if ts >= window_start
            ]
        if provider in self._request_windows:
            self._request_windows[provider] = [
                ts for ts in self._request_windows[provider] if ts >= window_start
            ]

    async def can_send(
        self,
        request_tokens: int,
        capability: ModelCapability,
    ) -> bool:
        """
        Evaluate if provider can accept request_tokens based on:
        1. In-memory cooloff
        2. Redis shared cooldown (if Redis active)
        3. Provider-reported remaining tokens/requests in response headers
        4. Configured rolling TPM / RPM limits
        """
        provider = capability.provider
        state = self._get_state(provider)
        self._check_cooloff(state)

        if state.rate_limited:
            return False

        # Check Redis distributed cooldown
        redis = self._get_redis()
        if redis is not None:
            try:
                cooldown_val = await redis.get(f"budget:cooldown:{provider}")
                if cooldown_val is not None:
                    state.rate_limited = True
                    try:
                        state.current_cooloff = float(cooldown_val)
                    except (ValueError, TypeError):
                        pass
                    return False
            except Exception as exc:
                logger.debug("[budget-manager] Redis cooldown check error: %s", exc)

        # Check provider-reported header constraints
        header_info = self._header_states.get(provider)
        if header_info:
            now_mono = time.monotonic()
            recorded_at = header_info.get("recorded_at", 0.0)
            elapsed = now_mono - recorded_at

            # Tokens reset independently from requests (typically sub-second or 1 minute)
            token_reset = header_info.get("reset_tokens")
            if token_reset is None or token_reset <= 0:
                token_reset = 60.0
            if elapsed >= token_reset:
                header_info["remaining_tokens"] = None

            # Request quota reset
            req_reset = header_info.get("reset_requests")
            if req_reset is None or req_reset <= 0:
                req_reset = 60.0
            if elapsed >= req_reset:
                header_info["remaining_requests"] = None

            if header_info.get("remaining_tokens") is None and header_info.get("remaining_requests") is None:
                self._header_states.pop(provider, None)
            else:
                rem_tokens = header_info.get("remaining_tokens")
                if rem_tokens is not None and rem_tokens < request_tokens:
                    logger.warning(
                        "[budget-manager] Provider %r reported remaining tokens (%d) < requested (%d).",
                        provider,
                        rem_tokens,
                        request_tokens,
                    )
                    return False
                rem_requests = header_info.get("remaining_requests")
                if rem_requests is not None and rem_requests <= 0:
                    logger.warning("[budget-manager] Provider %r reported 0 remaining requests.", provider)
                    return False

        # Check rolling window TPM / RPM
        now = time.monotonic()
        self._clean_windows(provider, now)

        settings = get_settings()
        tpm_limit: Optional[int] = None
        rpm_limit: Optional[int] = None

        if provider == "groq":
            tpm_limit = getattr(settings, "groq_tpm_limit", 8000)
            rpm_limit = getattr(settings, "groq_rpm_limit", 30)

        if tpm_limit is not None and tpm_limit > 0:
            current_tokens = sum(tok for _, tok in self._token_windows.get(provider, []))
            if current_tokens + request_tokens > tpm_limit:
                logger.warning(
                    "[budget-manager] Provider %r TPM limit reached: %d + %d > %d.",
                    provider,
                    current_tokens,
                    request_tokens,
                    tpm_limit,
                )
                return False

        if rpm_limit is not None and rpm_limit > 0:
            current_requests = len(self._request_windows.get(provider, []))
            if current_requests >= rpm_limit:
                logger.warning(
                    "[budget-manager] Provider %r RPM limit reached: %d >= %d.",
                    provider,
                    current_requests,
                    rpm_limit,
                )
                return False

        return True

    async def record_success(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        await super().record_success(provider, model, tokens_used)
        now = time.monotonic()
        if provider not in self._token_windows:
            self._token_windows[provider] = []
        if provider not in self._request_windows:
            self._request_windows[provider] = []
        self._token_windows[provider].append((now, tokens_used))
        self._request_windows[provider].append(now)
        self._clean_windows(provider, now)

        if headers:
            parsed = parse_rate_limit_headers(headers)
            parsed["recorded_at"] = now
            self._header_states[provider] = parsed

        redis = self._get_redis()
        if redis is not None:
            try:
                await redis.delete(f"budget:cooldown:{provider}")
            except Exception as exc:
                logger.debug("[budget-manager] Redis cooldown clear error: %s", exc)

    async def record_rate_limit(
        self,
        provider: str,
        retry_after: int | float = 0,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        actual_retry_after = float(retry_after)
        if headers:
            parsed = parse_rate_limit_headers(headers)
            parsed["recorded_at"] = time.monotonic()
            self._header_states[provider] = parsed
            if actual_retry_after <= 0 and parsed.get("retry_after") is not None:
                actual_retry_after = float(parsed["retry_after"])

        if actual_retry_after <= 0:
            actual_retry_after = self._default_cooloff

        await super().record_rate_limit(provider, int(round(actual_retry_after)))
        state = self._get_state(provider)
        state.current_cooloff = actual_retry_after

        redis = self._get_redis()
        if redis is not None:
            try:
                ttl = max(1, int(round(actual_retry_after)))
                await redis.set(f"budget:cooldown:{provider}", str(actual_retry_after), ex=ttl)
            except Exception as exc:
                logger.debug("[budget-manager] Redis cooldown set error: %s", exc)

    def reset(self, provider: str) -> None:
        super().reset(provider)
        self._token_windows.pop(provider, None)
        self._request_windows.pop(provider, None)
        self._header_states.pop(provider, None)

    def get_provider_status(self, provider: str) -> dict:
        """Return rich inspection status of provider quota, cooloff, and health."""
        state = self._get_state(provider)
        self._check_cooloff(state)
        now = time.monotonic()
        self._clean_windows(provider, now)

        elapsed = now - state.rate_limited_since if state.rate_limited else 0.0
        retry_after_remaining = max(0.0, state.current_cooloff - elapsed) if state.rate_limited else 0.0

        header_info = self._header_states.get(provider, {})
        remaining_tokens = header_info.get("remaining_tokens")
        remaining_requests = header_info.get("remaining_requests")
        recorded_at = header_info.get("recorded_at", 0.0)
        elapsed_header = now - recorded_at if recorded_at else 0.0

        token_reset = header_info.get("reset_tokens") or 60.0
        if elapsed_header >= token_reset:
            remaining_tokens = None
        req_reset = header_info.get("reset_requests") or 60.0
        if elapsed_header >= req_reset:
            remaining_requests = None

        if remaining_tokens is None and remaining_requests is None:
            self._header_states.pop(provider, None)

        is_exhausted = (
            (remaining_tokens is not None and remaining_tokens <= 0)
            or (remaining_requests is not None and remaining_requests <= 0)
        )

        if state.rate_limited:
            status_str = "cooldown"
        elif is_exhausted:
            status_str = "exhausted"
        else:
            status_str = "ready"

        return {
            "provider": provider,
            "available": not state.rate_limited and not is_exhausted,
            "rate_limited": state.rate_limited,
            "status": status_str,
            "retry_after_remaining": retry_after_remaining,
            "current_cooloff": state.current_cooloff,
            "success_count": state.success_count,
            "rate_limit_count": state.rate_limit_count,
            "total_tokens_used": state.total_tokens_used,
            "rolling_window_tokens": sum(tok for _, tok in self._token_windows.get(provider, [])),
            "rolling_window_requests": len(self._request_windows.get(provider, [])),
            "header_remaining_tokens": remaining_tokens,
            "header_remaining_requests": remaining_requests,
            "default_cooloff_seconds": self._default_cooloff,
        }

    def is_queued(self, provider: str) -> bool:
        """True if provider is currently in cooldown or capacity exhausted."""
        status = self.get_provider_status(provider)
        return not status["available"]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Singleton budget manager used across the backend.
budget_manager: ProviderBudgetManager = ProductionProviderBudgetManager()
