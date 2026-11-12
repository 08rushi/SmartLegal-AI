"""
budget.py — Isolated Shadow Budget & Provider Quota Manager (Phase 9).
Enforces strict financial caps and provider cooldowns completely isolated from production.
"""

from __future__ import annotations

import datetime
import logging
import time
from typing import Optional, Tuple

from config import get_settings
from shadow.config import get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")


class ShadowBudgetManager:
    """
    Manages quotas and financial spend exclusively for candidate models in shadow execution.
    All keys are strictly namespaced under 'shadow:budget:*' to prevent any interference
    with citizen-facing production rate limits.
    """

    def __init__(self):
        self._in_memory_spend: dict[str, float] = {}
        self._in_memory_cooldowns: dict[str, float] = {}

    def _get_today_key(self) -> str:
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        return f"shadow:budget:daily_spend:{today}"

    def _get_cooldown_key(self, provider: str) -> str:
        return f"shadow:budget:cooldown:{provider.lower()}"

    async def _get_redis(self):
        try:
            import cache
            return cache._redis
        except Exception:
            return None

    def calculate_cost_usd(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on configured token rates."""
        settings = get_shadow_settings()
        input_cost = (prompt_tokens / 1_000_000.0) * settings.shadow_cost_per_million_input_tokens
        output_cost = (completion_tokens / 1_000_000.0) * settings.shadow_cost_per_million_output_tokens
        return round(input_cost + output_cost, 6)

    async def get_daily_spend(self) -> float:
        """Retrieve total accumulated spend for today in USD."""
        r = await self._get_redis()
        today_key = self._get_today_key()
        if r is not None:
            try:
                val = await r.get(today_key)
                return float(val) if val is not None else 0.0
            except Exception as exc:
                logger.warning("[SHADOW-BUDGET] Failed to read spend from Redis: %s", exc)

        return self._in_memory_spend.get(today_key, 0.0)

    async def get_cooldown_remaining(self, provider: str) -> float:
        """Return remaining cooldown seconds for candidate provider, or 0.0 if ready."""
        r = await self._get_redis()
        cd_key = self._get_cooldown_key(provider)
        if r is not None:
            try:
                ttl = await r.ttl(cd_key)
                return float(max(0, ttl))
            except Exception as exc:
                logger.warning("[SHADOW-BUDGET] Failed to read cooldown from Redis: %s", exc)

        expire_at = self._in_memory_cooldowns.get(cd_key, 0.0)
        remaining = expire_at - time.time()
        return max(0.0, remaining)

    async def set_cooldown(self, provider: str, duration_seconds: float) -> None:
        """Apply cooldown lock to candidate provider."""
        duration = max(1.0, float(duration_seconds))
        r = await self._get_redis()
        cd_key = self._get_cooldown_key(provider)
        if r is not None:
            try:
                await r.set(cd_key, "1", ex=int(duration))
            except Exception as exc:
                logger.warning("[SHADOW-BUDGET] Failed to set cooldown in Redis: %s", exc)

        self._in_memory_cooldowns[cd_key] = time.time() + duration
        logger.info("[SHADOW-BUDGET] Candidate provider '%s' placed in cooldown for %.1fs", provider, duration)

    async def is_request_allowed(self, estimated_tokens: int = 12000) -> Tuple[bool, str]:
        """
        Check whether a shadow request is permitted under current provider cooldowns
        and daily spend ceilings.
        """
        settings = get_shadow_settings()
        provider = settings.shadow_candidate_provider

        # Check provider cooldown
        cooldown = await self.get_cooldown_remaining(provider)
        if cooldown > 0:
            return False, f"provider_in_cooldown_{int(cooldown)}s"

        # Check daily financial budget ceiling
        current_spend = await self.get_daily_spend()
        estimated_cost = self.calculate_cost_usd(estimated_tokens, settings.shadow_max_completion_tokens)
        if (current_spend + estimated_cost) > settings.shadow_daily_budget_usd:
            return False, "daily_budget_exhausted"

        return True, "allowed"

    async def record_usage(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Record actual token usage and accumulate daily spend in USD.
        Returns the computed cost for this specific execution.
        """
        cost = self.calculate_cost_usd(prompt_tokens, completion_tokens)
        r = await self._get_redis()
        today_key = self._get_today_key()

        if r is not None:
            try:
                # Atomically increment daily spend in Redis
                new_val = await r.incrbyfloat(today_key, cost)
                # Ensure 48-hour expiration
                await r.expire(today_key, 172800)
                logger.debug("[SHADOW-BUDGET] Recorded usage: $%.4f. Today total: $%.4f", cost, new_val)
                return cost
            except Exception as exc:
                logger.warning("[SHADOW-BUDGET] Failed to record usage in Redis: %s", exc)

        curr = self._in_memory_spend.get(today_key, 0.0)
        self._in_memory_spend[today_key] = curr + cost
        return cost

    async def reset(self) -> None:
        """Reset all in-memory and Redis budgets (primarily for testing)."""
        self._in_memory_spend.clear()
        self._in_memory_cooldowns.clear()
        r = await self._get_redis()
        if r is not None:
            try:
                today_key = self._get_today_key()
                await r.delete(today_key)
            except Exception:
                pass


_shadow_budget_manager_instance: Optional[ShadowBudgetManager] = None


def get_shadow_budget_manager() -> ShadowBudgetManager:
    """Return singleton instance of ShadowBudgetManager."""
    global _shadow_budget_manager_instance
    if _shadow_budget_manager_instance is None:
        _shadow_budget_manager_instance = ShadowBudgetManager()
    return _shadow_budget_manager_instance
