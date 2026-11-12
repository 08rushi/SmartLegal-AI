"""
ai_provider.py — AI Provider Abstraction & Fallback Engine (Phase 1 & Phase 5).

Provides provider-independent LLM orchestration interface (BaseAIProvider)
with Groq, OpenRouter, and Gemini adapters. Implements automatic controlled fallback
from primary provider (Groq) to secondary provider (OpenRouter) and tertiary (Gemini)
if rate-limited, timed out, or unavailable.

Key Phase 5 enhancements:
- OpenRouterProvider: High-reliability fallback client.
- ProviderQueuedError: Specialization of ProviderUnavailableError carrying retry_after
  and provider metadata when all providers are in cooloff.
- Zero fake successes: Always propagates errors so workers can update job state.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseAIProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        pass

    @abstractmethod
    async def generate_chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1800
    ) -> str:
        pass


class GroqProvider(BaseAIProvider):
    """Groq LLM Provider Adapter (Primary)."""

    @property
    def name(self) -> str:
        return "groq"

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        from services.groq_service import _call_groq
        return await _call_groq(prompt, max_tokens=max_tokens)

    async def generate_chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1800
    ) -> str:
        from services.groq_service import _call_groq_chat
        return await _call_groq_chat(messages, max_tokens=max_tokens)


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter LLM Provider Adapter (Secondary Fallback)."""

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        from services.openrouter_service import call_openrouter
        return await call_openrouter(prompt, max_tokens=max_tokens)

    async def generate_chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1800
    ) -> str:
        from services.openrouter_service import call_openrouter_chat
        return await call_openrouter_chat(messages, max_tokens=max_tokens)


class GeminiProvider(BaseAIProvider):
    """Gemini LLM Provider Adapter (Tertiary Fallback / Alternative)."""

    @property
    def name(self) -> str:
        return "gemini"

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        from services.gemini_service import _call_gemini
        return await _call_gemini(prompt)

    async def generate_chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1800
    ) -> str:
        prompt_text = "\n\n".join(
            [f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages]
        )
        from services.gemini_service import _call_gemini
        return await _call_gemini(prompt_text)


class ProviderUnavailableError(RuntimeError):
    """
    Raised by AIOrchestrator when every configured provider has failed.

    This exception must propagate to the worker/task layer so it can mark
    the analysis job as FAILED in the database. It must NEVER be caught
    and silently converted into a fabricated success response.
    """


class ProviderQueuedError(ProviderUnavailableError):
    """
    Raised when all candidate providers are temporarily rate-limited or in cooloff.
    Subclasses ProviderUnavailableError so existing exception handlers catch it,
    while exposing retry_after and providers for queue scheduling.
    """

    def __init__(
        self,
        message: str,
        retry_after: float = 60.0,
        providers: Optional[List[str]] = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.providers = providers or []


class AIOrchestrator:
    """
    AI Orchestrator with Controlled Multi-Provider Fallback.

    Primary:    Groq
    Secondary:  OpenRouter (when OPENROUTER_API_KEY is configured and enabled)
    Tertiary:   Gemini (when GEMINI_API_KEY is configured)

    Failure behaviour:
    - If all providers are in cooloff/rate-limited: raises ProviderQueuedError.
    - If all providers failed: raises ProviderUnavailableError.
    - No fabricated JSON or swallowed errors.
    """

    def __init__(self) -> None:
        self.groq = GroqProvider()
        self.openrouter = OpenRouterProvider()
        self.gemini = GeminiProvider()

    def _is_openrouter_active(self) -> bool:
        """True only if openrouter is configured with a real string key and enabled."""
        key = getattr(settings, "openrouter_api_key", None)
        enabled = getattr(settings, "openrouter_enabled", True)
        return isinstance(key, str) and bool(key.strip()) and (enabled is True)

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        primary_exc: Optional[Exception] = None
        openrouter_exc: Optional[Exception] = None

        # 1. Primary: Groq
        try:
            return await self.groq.generate_completion(prompt, max_tokens=max_tokens)
        except Exception as exc:
            primary_exc = exc
            logger.warning(
                "[ai-orchestrator] Primary provider Groq failed: %s. Attempting fallback...",
                exc,
            )

        # 2. Secondary: OpenRouter
        if self._is_openrouter_active():
            try:
                return await self.openrouter.generate_completion(prompt, max_tokens=max_tokens)
            except Exception as or_exc:
                openrouter_exc = or_exc
                logger.warning(
                    "[ai-orchestrator] Fallback provider OpenRouter failed: %s",
                    or_exc,
                )

        # 3. Tertiary: Gemini
        gemini_key = getattr(settings, "gemini_api_key", None)
        if gemini_key:
            try:
                return await self.gemini.generate_completion(prompt, max_tokens=max_tokens)
            except Exception as g_exc:
                logger.error("[ai-orchestrator] Fallback provider Gemini also failed: %s", g_exc)

        # 4. Check for queued / rate-limit state
        errors = [str(primary_exc)]
        if openrouter_exc:
            errors.append(str(openrouter_exc))
        rate_limited = any(
            "429" in e.lower() or "rate limit" in e.lower() or "cooldown" in e.lower()
            for e in errors
        )

        if rate_limited and not gemini_key:
            from services.provider_budget_manager import budget_manager
            groq_status = (
                budget_manager.get_provider_status("groq")
                if hasattr(budget_manager, "get_provider_status")
                else {}
            )
            retry_after = groq_status.get("retry_after_remaining", 60.0) or 60.0
            raise ProviderQueuedError(
                f"All configured providers are rate-limited or in cooloff. Retry after {retry_after:.1f}s.",
                retry_after=retry_after,
                providers=["groq", "openrouter"] if self._is_openrouter_active() else ["groq"],
            )

        raise ProviderUnavailableError(
            "All AI providers are unavailable. "
            f"Primary (Groq) error: {primary_exc}. "
            f"OpenRouter error: {openrouter_exc}. "
            "Gemini fallback was either not configured or also failed. "
            "The analysis job has been aborted — please retry later."
        )

    async def generate_chat_completion(
        self, messages: List[Dict[str, str]], max_tokens: int = 1800
    ) -> str:
        primary_exc: Optional[Exception] = None
        openrouter_exc: Optional[Exception] = None

        # 1. Primary: Groq
        try:
            return await self.groq.generate_chat_completion(messages, max_tokens=max_tokens)
        except Exception as exc:
            primary_exc = exc
            logger.warning(
                "[ai-orchestrator] Primary provider Groq failed: %s. Attempting fallback...",
                exc,
            )

        # 2. Secondary: OpenRouter
        if self._is_openrouter_active():
            try:
                return await self.openrouter.generate_chat_completion(messages, max_tokens=max_tokens)
            except Exception as or_exc:
                openrouter_exc = or_exc
                logger.warning(
                    "[ai-orchestrator] Fallback provider OpenRouter failed: %s",
                    or_exc,
                )

        # 3. Tertiary: Gemini
        gemini_key = getattr(settings, "gemini_api_key", None)
        if gemini_key:
            try:
                return await self.gemini.generate_chat_completion(messages, max_tokens=max_tokens)
            except Exception as g_exc:
                logger.error("[ai-orchestrator] Fallback provider Gemini also failed: %s", g_exc)

        # 4. Check for queued / rate-limit state
        errors = [str(primary_exc)]
        if openrouter_exc:
            errors.append(str(openrouter_exc))
        rate_limited = any(
            "429" in e.lower() or "rate limit" in e.lower() or "cooldown" in e.lower()
            for e in errors
        )

        if rate_limited and not gemini_key:
            from services.provider_budget_manager import budget_manager
            groq_status = (
                budget_manager.get_provider_status("groq")
                if hasattr(budget_manager, "get_provider_status")
                else {}
            )
            retry_after = groq_status.get("retry_after_remaining", 60.0) or 60.0
            raise ProviderQueuedError(
                f"All configured providers are rate-limited or in cooloff. Retry after {retry_after:.1f}s.",
                retry_after=retry_after,
                providers=["groq", "openrouter"] if self._is_openrouter_active() else ["groq"],
            )

        raise ProviderUnavailableError(
            "All AI providers are unavailable. "
            f"Primary (Groq) error: {primary_exc}. "
            f"OpenRouter error: {openrouter_exc}. "
            "Gemini fallback was either not configured or also failed. "
            "The chat request has been aborted — please retry later."
        )


# Global AI Orchestrator instance
ai_orchestrator = AIOrchestrator()
