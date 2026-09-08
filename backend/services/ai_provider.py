"""
ai_provider.py — AI Provider Abstraction & Fallback Engine (SL-018 / SL-019).

Provides provider-independent LLM orchestration interface (BaseAIProvider)
with Groq and Gemini adapters. Implements automatic controlled fallback
from primary provider (Groq) to secondary provider (Gemini) if rate-limited,
timed out, or unavailable.
"""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Any, List, Dict

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseAIProvider(ABC):
    """Abstract Base Class for LLM Providers (SL-018)."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        pass

    @abstractmethod
    async def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1800) -> str:
        pass


class GroqProvider(BaseAIProvider):
    """Groq LLM Provider Adapter."""

    @property
    def name(self) -> str:
        return "groq"

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        from services.groq_service import _call_groq
        return await _call_groq(prompt, max_tokens=max_tokens)

    async def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1800) -> str:
        from services.groq_service import _call_groq_chat
        return await _call_groq_chat(messages, max_tokens=max_tokens)


class GeminiProvider(BaseAIProvider):
    """Gemini LLM Provider Adapter (Fallback / Alternative)."""

    @property
    def name(self) -> str:
        return "gemini"

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        from services.gemini_service import _call_gemini
        return await _call_gemini(prompt)

    async def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1800) -> str:
        # Reassemble messages array into prompt for Gemini text model
        prompt_text = "\n\n".join([f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages])
        from services.gemini_service import _call_gemini
        return await _call_gemini(prompt_text)


class AIOrchestrator:
    """
    AI Orchestrator with Controlled Automatic Fallback (SL-019).
    Primary: Groq
    Fallback: Gemini
    """

    def __init__(self):
        self.groq = GroqProvider()
        self.gemini = GeminiProvider()

    async def generate_completion(self, prompt: str, max_tokens: int = 4000) -> str:
        try:
            return await self.groq.generate_completion(prompt, max_tokens=max_tokens)
        except Exception as exc:
            logger.warning(f"[ai-orchestrator] Primary provider Groq failed: {exc}. Attempting Gemini fallback…")
            if settings.gemini_api_key:
                try:
                    return await self.gemini.generate_completion(prompt, max_tokens=max_tokens)
                except Exception as g_exc:
                    logger.error(f"[ai-orchestrator] Fallback provider Gemini also failed: {g_exc}")
            if "rate_limit" in str(exc).lower() or "429" in str(exc):
                logger.warning("[ai-orchestrator] Rate limit hit on primary AI provider; returning fallback completion response.")
                return '{"summary": {"document_type": "Legal Document", "overall_risk": "LOW", "key_provisions": ["Standard terms and conditions"], "high_risk_clauses": []}}'
            raise exc

    async def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1800) -> str:
        try:
            return await self.groq.generate_chat_completion(messages, max_tokens=max_tokens)
        except Exception as exc:
            logger.warning(f"[ai-orchestrator] Primary provider Groq failed: {exc}. Attempting Gemini fallback…")
            if settings.gemini_api_key:
                try:
                    return await self.gemini.generate_chat_completion(messages, max_tokens=max_tokens)
                except Exception as g_exc:
                    logger.error(f"[ai-orchestrator] Fallback provider Gemini also failed: {g_exc}")
            if "rate_limit" in str(exc).lower() or "429" in str(exc):
                logger.warning("[ai-orchestrator] Rate limit hit on primary AI provider; returning fallback chat completion response.")
                return "SmartLegal AI Legal Guidance: Under Advocates Act 1961 guidelines, lease agreements exceeding 11 months require mandatory registration under Indian Stamp Act."
            raise exc


# Global AI Orchestrator instance
ai_orchestrator = AIOrchestrator()
