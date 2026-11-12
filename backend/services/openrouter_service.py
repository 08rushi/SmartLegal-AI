"""
openrouter_service.py — OpenRouter Fallback LLM Client (Phase 5).

Provides high-reliability fallback execution using OpenRouter API:
- Capability verification (context size, modalities, structured output)
- Provider budget manager integration (can_send, record_success, record_rate_limit)
- Defensive rate-limit header parsing
- Preserves zero-fake-success invariants
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from services.model_capabilities import (
    get_capability,
    get_openrouter_model,
    verify_model_capability,
)
from services.provider_budget_manager import budget_manager, parse_rate_limit_headers

logger = logging.getLogger(__name__)
settings = get_settings()


def is_openrouter_configured() -> bool:
    """Check if OpenRouter is configured with an API key and enabled."""
    key = getattr(settings, "openrouter_api_key", "")
    enabled = getattr(settings, "openrouter_enabled", True)
    return bool(isinstance(key, str) and key.strip() and enabled)


async def call_openrouter(
    prompt: str,
    max_tokens: int = 4000,
    model: Optional[str] = None,
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.1,
) -> str:
    """Convenience function for single-prompt completion via OpenRouter."""
    messages = [{"role": "user", "content": prompt}]
    return await call_openrouter_chat(
        messages=messages,
        max_tokens=max_tokens,
        model=model,
        response_format=response_format,
        temperature=temperature,
    )


async def call_openrouter_chat(
    messages: List[Dict[str, str]],
    max_tokens: int = 1800,
    model: Optional[str] = None,
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
) -> str:
    """
    Execute chat completion against OpenRouter API with full budget accounting.

    Raises:
        RuntimeError: If OpenRouter is not configured, rate-limited, or fails.
        ValueError: If selected model does not satisfy capability requirements.
    """
    if not is_openrouter_configured():
        raise RuntimeError("OpenRouter is not configured or is disabled.")

    target_model = model or get_openrouter_model()

    # 1. Capability verification
    required_structured = "json_schema" if response_format and response_format.get("type") == "json_object" else None
    is_ok, reason = verify_model_capability(
        model_name=target_model,
        required_context=max_tokens + 2000,
        required_structured_output=required_structured,
    )
    if not is_ok:
        raise ValueError(f"OpenRouter model {target_model} capability check failed: {reason}")

    # 2. Budget and rate-limit check
    cap = get_capability(target_model)
    can_send = await budget_manager.can_send(max_tokens, cap)
    if not can_send:
        status = budget_manager.get_provider_status("openrouter") if hasattr(budget_manager, "get_provider_status") else {}
        cooloff = status.get("retry_after_remaining", 60.0)
        raise RuntimeError(
            f"OpenRouter provider is currently unavailable or in cooldown ({cooloff:.1f}s remaining)."
        )

    # 3. HTTP Request construction
    base_url = getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1").rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key.strip()}",
        "HTTP-Referer": "https://smartlegal.ai",
        "X-Title": "SmartLegal AI",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": target_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    # 4. Asynchronous HTTP execution
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(endpoint, json=payload, headers=headers)
        except httpx.RequestError as exc:
            logger.error("[openrouter] Network error calling OpenRouter: %s", exc)
            raise RuntimeError(f"OpenRouter network error: {exc}") from exc

        # Rate-limiting handling
        if resp.status_code == 429:
            parsed_headers = parse_rate_limit_headers(resp.headers)
            retry_after = parsed_headers.get("retry_after") or 60.0
            await budget_manager.record_rate_limit(
                "openrouter",
                int(round(retry_after)),
                headers=dict(resp.headers),
            )
            logger.warning(
                "[openrouter] Received 429 Rate Limit. Cooloff for %.1fs. Body: %s",
                retry_after,
                resp.text[:200],
            )
            raise RuntimeError(f"OpenRouter rate limit 429 (retry after {retry_after:.1f}s): {resp.text[:200]}")

        if resp.status_code != 200:
            logger.error(
                "[openrouter] API call failed with status %d: %s",
                resp.status_code,
                resp.text[:300],
            )
            raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text[:300]}")

        # Parse success
        try:
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("OpenRouter returned empty choices array.")

            content = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens") or max_tokens

            # Account tokens in budget manager
            await budget_manager.record_success(
                provider="openrouter",
                model=target_model,
                tokens_used=total_tokens,
                headers=dict(resp.headers),
            )
            return content
        except Exception as exc:
            logger.error("[openrouter] Error parsing response: %s", exc)
            raise RuntimeError(f"Failed to parse OpenRouter response: {exc}") from exc
