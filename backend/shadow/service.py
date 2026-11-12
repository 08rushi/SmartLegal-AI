"""
service.py — Candidate Model Execution Service (Phase 9).
Executes candidate LLMs (Gemini 2.0 Flash / OpenRouter) via direct async httpx,
validating schemas and categorizing deterministic failures.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from pydantic import BaseModel, ValidationError

from services.analysis_schema import validate_analysis
from shadow.budget import get_shadow_budget_manager
from shadow.config import FailureCategory, get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")

# Standard prompt for Indian legal analysis parity testing
SHADOW_SYSTEM_PROMPT = """You are an expert Indian legal document analysis system.
You analyze Indian legal agreements (rental, employment, commercial, loans, NDAs).
Return your analysis strictly in valid JSON matching this schema:
{
  "summary": {
    "document_type": string,
    "overall_risk": "low" | "medium" | "high",
    "total_clauses": integer,
    "key_takeaways": [string]
  },
  "clauses": [
    {
      "clause_number": integer,
      "title": string,
      "text": string,
      "plain_english": string,
      "risk_level": "low" | "medium" | "high",
      "risk_explanation": string,
      "recommendations": [string],
      "statutory_references": [string]
    }
  ]
}
Ensure all JSON syntax is valid. Do not wrap in markdown fences."""


class ShadowExecutionResult(BaseModel):
    """Structured candidate execution outcome."""
    success: bool
    result_data: Dict[str, Any] = {}
    failure_category: Optional[FailureCategory] = None
    error_message: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    source_hash: str = ""
    started_at: str = ""
    completed_at: str = ""


class ShadowAnalysisService:
    """
    Candidate legal document analysis service.
    Direct async HTTP communication ensures zero external heavy SDK dependencies.
    """

    def __init__(self):
        self.settings = get_shadow_settings()
        self.budget_manager = get_shadow_budget_manager()

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def execute_candidate_analysis(
        self,
        document_text: str,
        document_id: str,
    ) -> ShadowExecutionResult:
        """
        Executes candidate LLM against extracted document text.
        Applies schema validation, failure classification, and budget accounting.
        """
        start_time = time.time()
        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        source_hash = self._compute_hash(document_text)

        # Truncate text if exceeding configured max tokens (approx 4 chars per token)
        max_chars = self.settings.shadow_max_prompt_tokens * 4
        truncated_text = document_text[:max_chars] if len(document_text) > max_chars else document_text

        # Budget allowance pre-check
        estimated_prompt_tokens = max(1, len(truncated_text) // 4)
        is_allowed, reason = await self.budget_manager.is_request_allowed(estimated_prompt_tokens)
        if not is_allowed:
            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            category = FailureCategory.SHADOW_RATE_LIMIT if "cooldown" in reason else FailureCategory.SHADOW_RESOURCE_LIMIT
            return ShadowExecutionResult(
                success=False,
                failure_category=category,
                error_message=f"Budget check denied: {reason}",
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )

        provider = self.settings.shadow_candidate_provider.lower()
        api_key = self.settings.shadow_candidate_api_key

        try:
            if provider == "google_genai":
                raw_json, prompt_tok, comp_tok = await self._call_google_genai(
                    truncated_text, api_key, self.settings.shadow_candidate_model
                )
            elif provider in ("openrouter", "groq"):
                raw_json, prompt_tok, comp_tok = await self._call_openrouter_compatible(
                    truncated_text, api_key, self.settings.shadow_candidate_model
                )
            else:
                # Mock candidate provider for deterministic testing/offline modes
                raw_json, prompt_tok, comp_tok = self._mock_candidate_response(truncated_text)

            # Record token usage & cost
            cost = await self.budget_manager.record_usage(prompt_tok, comp_tok)

            # Validate against production analysis schema
            validated_data = validate_analysis(raw_json)

            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            return ShadowExecutionResult(
                success=True,
                result_data=validated_data,
                prompt_tokens=prompt_tok,
                completion_tokens=comp_tok,
                estimated_cost_usd=cost,
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )

        except asyncio.TimeoutError:
            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return ShadowExecutionResult(
                success=False,
                failure_category=FailureCategory.SHADOW_TIMEOUT,
                error_message="Candidate API call timed out (300s limit exceeded)",
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )
        except httpx.HTTPStatusError as exc:
            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            status = exc.response.status_code

            if status in (401, 403):
                category = FailureCategory.SHADOW_AUTH_FAILURE
            elif status == 429:
                category = FailureCategory.SHADOW_RATE_LIMIT
                # Trigger isolated cooldown
                await self.budget_manager.set_cooldown(provider, 60.0)
            elif status >= 500:
                category = FailureCategory.SHADOW_PROVIDER_UNAVAILABLE
            else:
                category = FailureCategory.SHADOW_INTERNAL_ERROR

            return ShadowExecutionResult(
                success=False,
                failure_category=category,
                error_message=f"HTTP {status}: {str(exc)}",
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )
        except (json.JSONDecodeError, ValueError, ValidationError) as exc:
            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return ShadowExecutionResult(
                success=False,
                failure_category=FailureCategory.SHADOW_INVALID_OUTPUT,
                error_message=f"Candidate JSON schema violation: {str(exc)}",
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as exc:
            latency = int((time.time() - start_time) * 1000)
            completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return ShadowExecutionResult(
                success=False,
                failure_category=FailureCategory.SHADOW_INTERNAL_ERROR,
                error_message=f"Unexpected error: {str(exc)}",
                latency_ms=latency,
                source_hash=source_hash,
                started_at=started_at,
                completed_at=completed_at,
            )

    async def _call_google_genai(
        self,
        document_text: str,
        api_key: str,
        model: str,
    ) -> Tuple[Dict[str, Any], int, int]:
        """Direct REST call to Google Gemini 2.0 Flash."""
        if not api_key:
            # Fall back to mock if API key is not configured in environment
            return self._mock_candidate_response(document_text)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SHADOW_SYSTEM_PROMPT},
                        {"text": f"Document Text:\n{document_text}"},
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": self.settings.shadow_max_completion_tokens,
                "temperature": 0.1,
            },
        }

        async with httpx.AsyncClient(timeout=float(self.settings.shadow_job_timeout_seconds)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Parse Gemini response structure
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Google GenAI")

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            usage_meta = data.get("usageMetadata", {})
            prompt_tok = usage_meta.get("promptTokenCount", len(document_text) // 4)
            comp_tok = usage_meta.get("candidatesTokenCount", len(text_content) // 4)

            parsed_json = json.loads(text_content)
            return parsed_json, prompt_tok, comp_tok

    async def _call_openrouter_compatible(
        self,
        document_text: str,
        api_key: str,
        model: str,
    ) -> Tuple[Dict[str, Any], int, int]:
        """Direct REST call to OpenRouter or compatible OpenAI-style endpoint."""
        if not api_key:
            return self._mock_candidate_response(document_text)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://smartlegal.ai",
            "X-Title": "SmartLegal AI Shadow Pipeline",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SHADOW_SYSTEM_PROMPT},
                {"role": "user", "content": f"Document Text:\n{document_text}"},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=float(self.settings.shadow_job_timeout_seconds)) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tok = usage.get("prompt_tokens", len(document_text) // 4)
            comp_tok = usage.get("completion_tokens", len(content) // 4)

            parsed_json = json.loads(content)
            return parsed_json, prompt_tok, comp_tok

    def _mock_candidate_response(self, document_text: str) -> Tuple[Dict[str, Any], int, int]:
        """Provides deterministic mock analysis when API key is empty (development / test)."""
        prompt_tok = max(1, len(document_text) // 4)
        comp_tok = 250
        mock_data = {
            "summary": {
                "document_type": "Rental Agreement",
                "overall_risk": "medium",
                "total_clauses": 2,
                "key_takeaways": [
                    "Security deposit refund requires 30 days notice.",
                    "Subletting is strictly prohibited without landlord consent.",
                ],
            },
            "clauses": [
                {
                    "clause_number": 1,
                    "title": "Security Deposit",
                    "text": "The tenant agrees to deposit a refundable sum of Rs 50,000.",
                    "plain_english": "A refundable security deposit of Rs 50,000 is required.",
                    "risk_level": "medium",
                    "risk_explanation": "Notice period of 30 days is standard under Transfer of Property Act.",
                    "recommendations": ["Ensure receipt is provided in writing."],
                    "statutory_references": ["Transfer of Property Act, 1882"],
                },
                {
                    "clause_number": 2,
                    "title": "Maintenance and Repairs",
                    "text": "Tenant shall bear internal minor repairs up to Rs 1,000.",
                    "plain_english": "Tenant pays for small internal fixes up to Rs 1,000.",
                    "risk_level": "low",
                    "risk_explanation": "Standard balanced repair allocation.",
                    "recommendations": ["Inspect fixtures before signing."],
                    "statutory_references": [],
                },
            ],
        }
        return mock_data, prompt_tok, comp_tok
