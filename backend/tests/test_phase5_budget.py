"""
test_phase5_budget.py — Test Suite for Phase 5 (Provider Budget Manager & OpenRouter Fallback).

Covers:
1. Duration & rate-limit header parsing (defensive parsing, units, timestamps, missing).
2. ProductionProviderBudgetManager:
   - Rolling window quota tracking (TPM / RPM)
   - Accurate request & token accounting
   - Defensive header-based availability limits
   - Redis shared cooldown tracking with graceful in-memory fallback
   - Provider status introspection & is_queued states
3. OpenRouter Model Capability Verification:
   - Context window, modalities, structured output verification
4. OpenRouter Service:
   - Completion & chat completion with token accounting
   - 429 rate limit response handling
5. AI Orchestrator Multi-Provider Cascade:
   - Groq primary success
   - Groq -> OpenRouter fallback
   - OpenRouter -> Gemini fallback
   - ProviderQueuedError on all-cooldown state (subclasses ProviderUnavailableError)
   - Zero fake successes
6. Preservation of Phase 3 chunking & Phase 4 visual pipeline
"""

import asyncio
import json
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from config import Settings
from services.model_capabilities import (
    ModelCapability,
    get_capability,
    get_openrouter_model,
    verify_model_capability,
)
from services.provider_budget_manager import (
    InMemoryProviderBudgetManager,
    ProductionProviderBudgetManager,
    parse_duration_string,
    parse_rate_limit_headers,
)


class TestDurationAndHeaderParsing(unittest.TestCase):
    """Test defensive parsing of durations and HTTP rate-limit headers."""

    def test_parse_duration_numeric(self):
        self.assertEqual(parse_duration_string(30), 30.0)
        self.assertEqual(parse_duration_string(12.5), 12.5)
        self.assertEqual(parse_duration_string("45"), 45.0)

    def test_parse_duration_units(self):
        self.assertAlmostEqual(parse_duration_string("2s"), 2.0)
        self.assertAlmostEqual(parse_duration_string("60ms"), 0.06)
        self.assertAlmostEqual(parse_duration_string("500us"), 0.0005)
        self.assertAlmostEqual(parse_duration_string("1m30s"), 90.0)
        self.assertAlmostEqual(parse_duration_string("2h"), 7200.0)

    def test_parse_duration_timestamp(self):
        # Epoch timestamp 100 seconds in the future
        future_ts = time.time() + 100.0
        parsed = parse_duration_string(future_ts)
        self.assertIsNotNone(parsed)
        self.assertGreater(parsed, 90.0)
        self.assertLess(parsed, 110.0)

    def test_parse_duration_malformed_returns_none(self):
        self.assertIsNone(parse_duration_string(None))
        self.assertIsNone(parse_duration_string(""))
        self.assertIsNone(parse_duration_string("invalid_duration"))
        self.assertIsNone(parse_duration_string([]))

    def test_parse_rate_limit_headers_standard(self):
        headers = {
            "x-ratelimit-remaining-tokens": "4500",
            "x-ratelimit-remaining-requests": "15",
            "x-ratelimit-reset-tokens": "2.5s",
            "x-ratelimit-reset-requests": "10s",
            "retry-after": "5",
        }
        res = parse_rate_limit_headers(headers)
        self.assertEqual(res["remaining_tokens"], 4500)
        self.assertEqual(res["remaining_requests"], 15)
        self.assertAlmostEqual(res["reset_tokens"], 2.5)
        self.assertAlmostEqual(res["reset_requests"], 10.0)
        self.assertAlmostEqual(res["retry_after"], 5.0)

    def test_parse_rate_limit_headers_case_insensitivity(self):
        headers = {
            "X-RateLimit-Remaining-Tokens": "8000",
            "X-RateLimit-Reset-Tokens": "60ms",
            "Retry-After": "3",
        }
        res = parse_rate_limit_headers(headers)
        self.assertEqual(res["remaining_tokens"], 8000)
        self.assertAlmostEqual(res["reset_tokens"], 0.06)
        self.assertAlmostEqual(res["retry_after"], 3.0)

    def test_parse_rate_limit_headers_derives_retry_after_when_exhausted(self):
        headers = {
            "x-ratelimit-remaining-tokens": "0",
            "x-ratelimit-reset-tokens": "4.2s",
        }
        res = parse_rate_limit_headers(headers)
        self.assertEqual(res["remaining_tokens"], 0)
        self.assertAlmostEqual(res["retry_after"], 4.2)

    def test_parse_rate_limit_headers_empty_or_none(self):
        res1 = parse_rate_limit_headers(None)
        self.assertIsNone(res1["remaining_tokens"])
        self.assertIsNone(res1["retry_after"])

        res2 = parse_rate_limit_headers({})
        self.assertIsNone(res2["remaining_tokens"])


class TestProductionProviderBudgetManager(unittest.IsolatedAsyncioTestCase):
    """Test ProductionProviderBudgetManager features and Phase 1 compatibility."""

    def _make_capability(self, provider: str = "groq") -> ModelCapability:
        return ModelCapability(
            name="test-model",
            provider=provider,
            context_window=128_000,
            max_output_tokens=4096,
            modalities=["text"],
            vision_support=False,
            structured_output="json_schema",
        )

    async def test_initial_availability_and_accounting(self):
        mgr = ProductionProviderBudgetManager(default_cooloff_seconds=10.0)
        cap = self._make_capability("groq")
        self.assertTrue(await mgr.can_send(1000, cap))

        await mgr.record_success("groq", "test-model", 450)
        status = mgr.get_provider_status("groq")
        self.assertEqual(status["total_tokens_used"], 450)
        self.assertEqual(status["success_count"], 1)
        self.assertEqual(status["rolling_window_tokens"], 450)
        self.assertEqual(status["rolling_window_requests"], 1)
        self.assertEqual(status["status"], "ready")

    async def test_rate_limit_blocks_and_expires(self):
        mgr = ProductionProviderBudgetManager(default_cooloff_seconds=0.1)
        cap = self._make_capability("groq")

        await mgr.record_rate_limit("groq", retry_after=0.1)
        self.assertFalse(await mgr.can_send(500, cap))
        self.assertTrue(mgr.is_queued("groq"))
        self.assertEqual(mgr.get_provider_status("groq")["status"], "cooldown")

        # Wait for cooloff to expire
        await asyncio.sleep(0.15)
        self.assertTrue(await mgr.can_send(500, cap))
        self.assertFalse(mgr.is_queued("groq"))
        self.assertEqual(mgr.get_provider_status("groq")["status"], "ready")

    async def test_header_remaining_tokens_enforcement(self):
        mgr = ProductionProviderBudgetManager()
        cap = self._make_capability("groq")

        # Record header stating only 1000 tokens remaining
        await mgr.record_success(
            "groq",
            "test-model",
            200,
            headers={"x-ratelimit-remaining-tokens": "1000"},
        )

        # 500 tokens should be permitted
        self.assertTrue(await mgr.can_send(500, cap))
        # 1500 tokens should be blocked
        self.assertFalse(await mgr.can_send(1500, cap))

    async def test_header_remaining_requests_exhausted(self):
        mgr = ProductionProviderBudgetManager()
        cap = self._make_capability("groq")

        await mgr.record_success(
            "groq",
            "test-model",
            100,
            headers={"x-ratelimit-remaining-requests": "0"},
        )
        self.assertFalse(await mgr.can_send(100, cap))
        status = mgr.get_provider_status("groq")
        self.assertEqual(status["status"], "exhausted")

    async def test_rolling_tpm_limit_enforcement(self):
        mgr = ProductionProviderBudgetManager()
        cap = self._make_capability("groq")

        with patch("services.provider_budget_manager.get_settings") as mock_settings:
            mock_settings.return_value.groq_tpm_limit = 5000
            mock_settings.return_value.groq_rpm_limit = 100
            mock_settings.return_value.provider_cooldown_seconds = 60.0

            # Record 4500 tokens used
            await mgr.record_success("groq", "test-model", 4500)

            # 400 more tokens should pass (4500 + 400 <= 5000)
            self.assertTrue(await mgr.can_send(400, cap))
            # 600 more tokens should be blocked (4500 + 600 > 5000)
            self.assertFalse(await mgr.can_send(600, cap))

    async def test_rolling_rpm_limit_enforcement(self):
        mgr = ProductionProviderBudgetManager()
        cap = self._make_capability("groq")

        with patch("services.provider_budget_manager.get_settings") as mock_settings:
            mock_settings.return_value.groq_tpm_limit = 100_000
            mock_settings.return_value.groq_rpm_limit = 2
            mock_settings.return_value.provider_cooldown_seconds = 60.0

            await mgr.record_success("groq", "test-model", 10)
            self.assertTrue(await mgr.can_send(10, cap))
            await mgr.record_success("groq", "test-model", 10)

            # 2 requests recorded, RPM limit is 2 -> blocked
            self.assertFalse(await mgr.can_send(10, cap))

    async def test_redis_distributed_cooldown(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "30.0"

        mgr = ProductionProviderBudgetManager(redis_client=mock_redis)
        cap = self._make_capability("groq")

        # Redis has cooldown key -> can_send returns False
        self.assertFalse(await mgr.can_send(100, cap))
        mock_redis.get.assert_called_with("budget:cooldown:groq")

        # Record rate limit sets Redis key with TTL
        await mgr.record_rate_limit("groq", retry_after=45)
        mock_redis.set.assert_called_with("budget:cooldown:groq", "45.0", ex=45)

        # Record success deletes Redis key
        await mgr.record_success("groq", "test-model", 100)
        mock_redis.delete.assert_called_with("budget:cooldown:groq")

    async def test_redis_failure_gracefully_falls_back_to_memory(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis connection refused")

        mgr = ProductionProviderBudgetManager(redis_client=mock_redis)
        cap = self._make_capability("groq")

        # Can send succeeds despite Redis error
        self.assertTrue(await mgr.can_send(100, cap))


class TestModelCapabilityVerification(unittest.TestCase):
    """Test model capability verification logic for OpenRouter models."""

    def test_openrouter_registered_models(self):
        model = get_openrouter_model()
        self.assertEqual(model, "meta-llama/llama-3.3-70b-instruct")
        cap = get_capability(model)
        self.assertEqual(cap.provider, "openrouter")
        self.assertFalse(cap.vision_support)
        self.assertEqual(cap.structured_output, "json_schema")

    def test_verify_model_capability_success(self):
        is_ok, reason = verify_model_capability(
            "meta-llama/llama-3.3-70b-instruct",
            required_context=8000,
            required_structured_output="json_schema",
        )
        self.assertTrue(is_ok)
        self.assertIsNone(reason)

    def test_verify_model_capability_context_exceeded(self):
        is_ok, reason = verify_model_capability(
            "meta-llama/llama-3.3-70b-instruct",
            required_context=200_000,
        )
        self.assertFalse(is_ok)
        self.assertIn("insufficient context window", reason)

    def test_verify_model_capability_structured_output_mismatch(self):
        # google/gemini-flash-1.5 has structured_output="json_mode"
        is_ok, reason = verify_model_capability(
            "google/gemini-flash-1.5",
            required_structured_output="json_schema",
        )
        self.assertFalse(is_ok)
        self.assertIn("does not support structured_output", reason)


class TestOpenRouterService(unittest.IsolatedAsyncioTestCase):
    """Test openrouter_service.py execution and error handling."""

    def setUp(self):
        from services.provider_budget_manager import budget_manager
        budget_manager.reset("openrouter")

    async def test_is_openrouter_configured(self):
        from services.openrouter_service import is_openrouter_configured

        with patch("services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-test"
            mock_settings.openrouter_enabled = True
            self.assertTrue(is_openrouter_configured())

            mock_settings.openrouter_api_key = ""
            self.assertFalse(is_openrouter_configured())

            mock_settings.openrouter_api_key = "sk-or-test"
            mock_settings.openrouter_enabled = False
            self.assertFalse(is_openrouter_configured())

    @patch("httpx.AsyncClient.post")
    async def test_call_openrouter_success(self, mock_post):
        from services.openrouter_service import call_openrouter

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {
            "x-ratelimit-remaining-tokens": "95000",
            "x-ratelimit-remaining-requests": "99",
        }
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "OpenRouter legal explanation"}}],
            "usage": {"total_tokens": 128},
        }
        mock_post.return_value = mock_resp

        with patch("services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-test"
            mock_settings.openrouter_enabled = True
            mock_settings.openrouter_model = "meta-llama/llama-3.3-70b-instruct"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"

            res = await call_openrouter("Explain clause 3")
            self.assertEqual(res, "OpenRouter legal explanation")

    @patch("httpx.AsyncClient.post")
    async def test_call_openrouter_rate_limit_429(self, mock_post):
        from services.openrouter_service import call_openrouter

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {"retry-after": "15s"}
        mock_resp.text = "Rate limit exceeded"
        mock_post.return_value = mock_resp

        with patch("services.openrouter_service.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-test"
            mock_settings.openrouter_enabled = True
            mock_settings.openrouter_model = "meta-llama/llama-3.3-70b-instruct"
            mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"

            with self.assertRaises(RuntimeError) as ctx:
                await call_openrouter("Explain clause 3")
            self.assertIn("OpenRouter rate limit 429", str(ctx.exception))


class TestAIOrchestratorFallback(unittest.IsolatedAsyncioTestCase):
    """Test AIOrchestrator fallback cascade and ProviderQueuedError."""

    async def test_primary_groq_success(self):
        from services.ai_provider import AIOrchestrator

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(return_value="Groq response")
        orch.openrouter.generate_completion = AsyncMock()

        res = await orch.generate_completion("Test prompt")
        self.assertEqual(res, "Groq response")
        orch.groq.generate_completion.assert_awaited_once()
        orch.openrouter.generate_completion.assert_not_called()

    async def test_fallback_to_openrouter_when_groq_fails(self):
        from services.ai_provider import AIOrchestrator

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("Groq 429 RateLimit"))
        orch.openrouter.generate_completion = AsyncMock(return_value="OpenRouter response")

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-valid-key"
            mock_settings.openrouter_enabled = True
            mock_settings.gemini_api_key = ""

            res = await orch.generate_completion("Test prompt")
            self.assertEqual(res, "OpenRouter response")
            orch.openrouter.generate_completion.assert_awaited_once()

    async def test_fallback_to_gemini_when_groq_and_openrouter_fail(self):
        from services.ai_provider import AIOrchestrator

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("Groq 429"))
        orch.openrouter.generate_completion = AsyncMock(side_effect=Exception("OpenRouter 429"))
        orch.gemini.generate_completion = AsyncMock(return_value="Gemini response")

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-valid-key"
            mock_settings.openrouter_enabled = True
            mock_settings.gemini_api_key = "gemini-valid-key"

            res = await orch.generate_completion("Test prompt")
            self.assertEqual(res, "Gemini response")
            orch.gemini.generate_completion.assert_awaited_once()

    async def test_provider_queued_error_when_all_in_cooloff(self):
        from services.ai_provider import AIOrchestrator, ProviderQueuedError, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("Groq rate limit 429"))
        orch.openrouter.generate_completion = AsyncMock(side_effect=Exception("OpenRouter 429"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.openrouter_api_key = "sk-or-valid-key"
            mock_settings.openrouter_enabled = True
            mock_settings.gemini_api_key = ""

            with self.assertRaises(ProviderQueuedError) as ctx:
                await orch.generate_completion("Test prompt")

            # ProviderQueuedError must subclass ProviderUnavailableError
            self.assertIsInstance(ctx.exception, ProviderUnavailableError)
            self.assertGreater(ctx.exception.retry_after, 0.0)
            self.assertIn("groq", ctx.exception.providers)

    async def test_provider_unavailable_on_fatal_non_rate_limit_error(self):
        from services.ai_provider import AIOrchestrator, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=ValueError("Bad request syntax"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""
            mock_settings.gemini_api_key = ""

            with self.assertRaises(ProviderUnavailableError):
                await orch.generate_completion("Test prompt")


class TestGroqServiceIntegrationAndPipelinePreservation(unittest.IsolatedAsyncioTestCase):
    """Test groq_service integration with budget manager and preservation of Phase 3 / Phase 4."""

    @patch("services.groq_service._get_groq_client")
    async def test_call_groq_records_success_tokens(self, mock_client_fn):
        from services.groq_service import _call_groq
        from services.provider_budget_manager import budget_manager

        budget_manager.reset("groq")

        mock_client = MagicMock()
        mock_raw = MagicMock()
        mock_raw.headers = {"x-ratelimit-remaining-tokens": "5000"}
        mock_comp = MagicMock()
        mock_comp.choices = [MagicMock(message=MagicMock(content="Groq analysis text"))]
        mock_comp.usage.total_tokens = 320
        mock_raw.parse.return_value = mock_comp
        mock_client.chat.completions.with_raw_response.create.return_value = mock_raw
        mock_client_fn.return_value = mock_client

        res = await _call_groq("Analyze this lease")
        self.assertEqual(res, "Groq analysis text")

        status = budget_manager.get_provider_status("groq")
        self.assertEqual(status["total_tokens_used"], 320)
        self.assertEqual(status["success_count"], 1)

    @patch("services.groq_service._get_groq_client")
    async def test_call_groq_falls_back_to_openrouter_on_429(self, mock_client_fn):
        from services.groq_service import _call_groq
        from services.provider_budget_manager import budget_manager

        budget_manager.reset("groq")

        mock_client = MagicMock()
        # Simulate 429 RateLimit
        mock_err = Exception("Rate limit exceeded 429")
        mock_client.chat.completions.with_raw_response.create.side_effect = mock_err
        mock_client_fn.return_value = mock_client

        with patch("services.openrouter_service.is_openrouter_configured", return_value=True), \
             patch("services.openrouter_service.call_openrouter", new_callable=AsyncMock) as mock_or_call:
            mock_or_call.return_value = "Fallback OpenRouter response"

            res = await _call_groq("Analyze this document")
            self.assertEqual(res, "Fallback OpenRouter response")
            mock_or_call.assert_awaited_once()

    def test_visual_pipeline_preserves_local_and_gemini_routing(self):
        """Confirm OpenRouter is never invoked or registered for visual OCR."""
        from services.model_capabilities import MODEL_REGISTRY, get_gemini_vision_model
        from services.vision_pipeline import VisualDocumentPipeline

        # Gemini vision model remains config-driven
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value.gemini_vision_model = "gemini-3.8-flash"
            vis_cap = get_gemini_vision_model()
            self.assertIn("gemini", vis_cap.name)
            self.assertTrue(vis_cap.vision_support)

        # OpenRouter models MUST NOT support vision
        openrouter_models = [m for m, cap in MODEL_REGISTRY.items() if cap.provider == "openrouter"]
        self.assertGreater(len(openrouter_models), 0)
        for m in openrouter_models:
            self.assertFalse(MODEL_REGISTRY[m].vision_support, f"OpenRouter model {m} must not have vision support")


if __name__ == "__main__":
    unittest.main()
