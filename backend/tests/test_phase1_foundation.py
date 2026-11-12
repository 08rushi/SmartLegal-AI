"""
tests/test_phase1_foundation.py — Phase 1 Foundation Unit Tests.

Covers:
  1. ProviderBudgetManager — async interface, recording, rate-limit blocking,
     retry_after cooloff, reset, stats.
  2. ModelCapability Registry — lookup, list, Gemini validation
     (missing / invalid / valid model). Tests use Gemini 3.x model IDs.
  3. Unified JSON Parsing — valid JSON dict/str, markdown fences, malformed
     repair, schema validation failure.
  4. Fake-success removal — ProviderUnavailableError is raised (not a fabricated
     string).

These tests run without any external services (no DB, no Groq, no Gemini API).
"""

from __future__ import annotations

import json
import os
import sys
import time
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup — ensure backend/ is importable when running from backend/tests/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ===========================================================================
# 1. ProviderBudgetManager tests  (async interface)
# ===========================================================================

class TestInMemoryProviderBudgetManager(unittest.IsolatedAsyncioTestCase):
    """Tests for the Phase 1 in-memory ProviderBudgetManager."""

    def _make_capability(self, provider: str = "groq", name: str = "openai/gpt-oss-120b"):
        from services.model_capabilities import ModelCapability
        return ModelCapability(
            name=name,
            provider=provider,
            context_window=131_072,
            max_output_tokens=16_384,
            modalities=["text"],
            vision_support=False,
            structured_output="json_schema",
        )

    def _make_mgr(self, cooloff: float = 5.0):
        from services.provider_budget_manager import InMemoryProviderBudgetManager
        return InMemoryProviderBudgetManager(default_cooloff_seconds=cooloff)

    # --- Basic availability ---

    async def test_new_provider_is_available(self):
        mgr = self._make_mgr()
        cap = self._make_capability("groq")
        self.assertTrue(await mgr.can_send(1000, cap))

    async def test_record_success_increments_counter(self):
        mgr = self._make_mgr()
        await mgr.record_success("groq", "openai/gpt-oss-120b", 500)
        await mgr.record_success("groq", "openai/gpt-oss-120b", 300)
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["success_count"], 2)
        self.assertEqual(stats["total_tokens_used"], 800)

    async def test_record_success_tracks_tokens(self):
        mgr = self._make_mgr()
        await mgr.record_success("groq", "openai/gpt-oss-120b", 1234)
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["total_tokens_used"], 1234)

    # --- Rate-limit blocking ---

    async def test_record_rate_limit_blocks_provider(self):
        mgr = self._make_mgr()
        cap = self._make_capability("groq")
        await mgr.record_rate_limit("groq", retry_after=60)
        self.assertFalse(await mgr.can_send(1000, cap))

    async def test_rate_limit_count_increments(self):
        mgr = self._make_mgr()
        await mgr.record_rate_limit("groq", retry_after=30)
        await mgr.record_rate_limit("groq", retry_after=30)
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["rate_limit_count"], 2)

    async def test_success_after_rate_limit_clears_flag(self):
        mgr = self._make_mgr()
        cap = self._make_capability("groq")
        await mgr.record_rate_limit("groq", retry_after=60)
        self.assertFalse(await mgr.can_send(100, cap))
        await mgr.record_success("groq", "openai/gpt-oss-120b", 100)
        self.assertTrue(await mgr.can_send(100, cap))

    async def test_retry_after_zero_uses_default_cooloff(self):
        """retry_after=0 should fall back to default_cooloff_seconds."""
        mgr = self._make_mgr(cooloff=30.0)
        await mgr.record_rate_limit("groq", retry_after=0)
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["current_cooloff"], 30.0)

    async def test_retry_after_nonzero_overrides_default(self):
        """retry_after>0 should be used as the cooloff, not the default."""
        mgr = self._make_mgr(cooloff=30.0)
        await mgr.record_rate_limit("groq", retry_after=90)
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["current_cooloff"], 90.0)

    # --- Cooloff expiry ---

    async def test_cooloff_expires_after_duration(self):
        mgr = self._make_mgr(cooloff=0.05)
        cap = self._make_capability("groq")
        await mgr.record_rate_limit("groq", retry_after=0)
        self.assertFalse(await mgr.can_send(100, cap))
        time.sleep(0.12)  # Wait for cooloff to elapse
        self.assertTrue(await mgr.can_send(100, cap))

    # --- Reset ---

    async def test_reset_clears_state(self):
        mgr = self._make_mgr()
        await mgr.record_success("groq", "model", 500)
        await mgr.record_rate_limit("groq", retry_after=30)
        mgr.reset("groq")
        stats = mgr.get_stats("groq")
        self.assertEqual(stats["success_count"], 0)
        self.assertEqual(stats["rate_limit_count"], 0)
        self.assertFalse(stats["rate_limited"])

    async def test_reset_nonexistent_provider_is_safe(self):
        mgr = self._make_mgr()
        mgr.reset("unknown_provider")  # Must not raise

    # --- Provider isolation ---

    async def test_providers_are_isolated(self):
        mgr = self._make_mgr()
        groq_cap = self._make_capability("groq")
        gemini_cap = self._make_capability("gemini", "gemini-3.8-flash")
        await mgr.record_rate_limit("groq", retry_after=60)
        self.assertFalse(await mgr.can_send(100, groq_cap))
        self.assertTrue(await mgr.can_send(100, gemini_cap))  # Unaffected

    # --- Stats snapshot ---

    async def test_get_stats_returns_correct_shape(self):
        mgr = self._make_mgr()
        await mgr.record_success("openrouter", "some-model", 200)
        stats = mgr.get_stats("openrouter")
        for key in ("provider", "available", "success_count", "rate_limit_count",
                    "total_tokens_used", "rate_limited", "rate_limited_since",
                    "current_cooloff", "default_cooloff_seconds"):
            self.assertIn(key, stats, f"Missing key: {key}")
        self.assertEqual(stats["provider"], "openrouter")
        self.assertTrue(stats["available"])

    async def test_can_send_passes_tokens_and_capability(self):
        """can_send should accept any request_tokens value without error."""
        mgr = self._make_mgr()
        cap = self._make_capability("groq")
        # Should not raise regardless of token count
        self.assertTrue(await mgr.can_send(0, cap))
        self.assertTrue(await mgr.can_send(999_999, cap))


# ===========================================================================
# 2. ModelCapability Registry tests
# ===========================================================================

class TestModelCapabilityRegistry(unittest.TestCase):

    def test_get_known_groq_model(self):
        from services.model_capabilities import get_capability
        cap = get_capability("openai/gpt-oss-120b")
        self.assertIsNotNone(cap)
        self.assertEqual(cap.provider, "groq")
        self.assertEqual(cap.context_window, 131_072)
        self.assertEqual(cap.structured_output, "json_schema")
        self.assertFalse(cap.vision_support)

    def test_get_unknown_model_returns_none(self):
        from services.model_capabilities import get_capability
        self.assertIsNone(get_capability("nonexistent/model-99b"))

    def test_list_models_returns_multiple(self):
        from services.model_capabilities import list_models
        models = list_models()
        self.assertGreater(len(models), 1)

    def test_all_registered_models_have_required_fields(self):
        from services.model_capabilities import list_models
        for cap in list_models():
            self.assertIsInstance(cap.name, str)
            self.assertIsInstance(cap.provider, str)
            self.assertGreater(cap.context_window, 0)
            self.assertGreater(cap.max_output_tokens, 0)
            self.assertIn(cap.structured_output, ("json_schema", "json_object", "none"))
            self.assertIsInstance(cap.modalities, list)

    def test_gemini_models_have_vision_support(self):
        from services.model_capabilities import list_models
        for cap in list_models():
            if cap.provider == "gemini":
                self.assertTrue(
                    cap.vision_support,
                    f"{cap.name} should have vision_support=True",
                )

    def test_no_retired_gemini_15_or_20_models_in_registry(self):
        """Retired Gemini 1.5 and 2.0 model IDs must not appear in the registry.
        (2.5 is intentionally allowed: it is GA and listed by the live Gemini API.)"""
        from services.model_capabilities import KNOWN_GEMINI_MODELS
        retired_prefixes = ("gemini-1.5", "gemini-2.0")
        for model_name in KNOWN_GEMINI_MODELS:
            for prefix in retired_prefixes:
                self.assertFalse(
                    model_name.startswith(prefix),
                    f"Retired model {model_name!r} must not be in the registry.",
                )

    def test_known_gemini_models_are_3x_series(self):
        """Registry should contain current Gemini 3.x models."""
        from services.model_capabilities import KNOWN_GEMINI_MODELS
        has_3x = any(name.startswith("gemini-3.") for name in KNOWN_GEMINI_MODELS)
        self.assertTrue(has_3x, "Registry must contain at least one Gemini 3.x model.")

    # --- Gemini vision model validation ---

    def test_get_gemini_vision_model_raises_when_not_configured(self):
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="")
            with self.assertRaises(EnvironmentError) as ctx:
                get_gemini_vision_model()
            self.assertIn("GEMINI_VISION_MODEL", str(ctx.exception))

    def test_get_gemini_vision_model_raises_for_unknown_model(self):
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="gemini-obsolete-model")
            with self.assertRaises(ValueError) as ctx:
                get_gemini_vision_model()
            self.assertIn("not a recognized", str(ctx.exception))

    def test_get_gemini_vision_model_raises_for_retired_gemini_15(self):
        """Retired gemini-1.5-flash must be rejected."""
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="gemini-1.5-flash")
            with self.assertRaises(ValueError):
                get_gemini_vision_model()

    def test_get_gemini_vision_model_raises_for_retired_gemini_20(self):
        """Retired gemini-2.0-flash must be rejected."""
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="gemini-2.0-flash")
            with self.assertRaises(ValueError):
                get_gemini_vision_model()

    def test_get_gemini_vision_model_succeeds_for_current_38_flash(self):
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="gemini-3.8-flash")
            cap = get_gemini_vision_model()
            self.assertEqual(cap.name, "gemini-3.8-flash")
            self.assertTrue(cap.vision_support)
            self.assertEqual(cap.structured_output, "json_schema")

    def test_get_gemini_vision_model_succeeds_for_35_flash_lite(self):
        from services.model_capabilities import get_gemini_vision_model
        with patch("services.model_capabilities.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_vision_model="gemini-3.5-flash-lite")
            cap = get_gemini_vision_model()
            self.assertEqual(cap.name, "gemini-3.5-flash-lite")
            self.assertTrue(cap.vision_support)


# ===========================================================================
# 3. Unified JSON Parsing tests
# ===========================================================================

class TestExtractJsonFromText(unittest.TestCase):

    def setUp(self):
        from services.ai_parser import extract_json_from_text
        self.extract = extract_json_from_text

    def test_plain_json_object(self):
        result = self.extract('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_markdown_fence(self):
        raw = '```json\n{"summary": "ok", "clauses": []}\n```'
        result = self.extract(raw)
        self.assertIsInstance(result, dict)

    def test_json_with_preamble_text(self):
        # Object-first extraction: the outer {} is found before any inner []
        raw = 'Here is the analysis:\n\n{"summary": {"document_type": "Lease"}, "clauses": []}'
        result = self.extract(raw)
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)

    def test_trailing_comma_repair_object(self):
        raw = '{"a": 1, "b": 2,}'
        result = self.extract(raw)
        self.assertEqual(result["a"], 1)

    def test_trailing_comma_repair_array(self):
        raw = '[{"a": 1}, {"b": 2},]'
        result = self.extract(raw)
        self.assertEqual(len(result), 2)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            self.extract("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            self.extract("   ")

    def test_unparseable_text_raises(self):
        with self.assertRaises(ValueError):
            self.extract("This is just plain text with no JSON whatsoever")

    def test_json_array_extracted(self):
        raw = 'Result: [{"id": "1"}, {"id": "2"}]'
        result = self.extract(raw)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)


class TestParseAiResponse(unittest.TestCase):
    """Test the unified parse_ai_response entry point."""

    def _make_valid_raw(self) -> dict:
        return {
            "summary": {
                "document_type": "Lease",
                "overall_risk": "low",
            },
            "clauses": [
                {
                    "id": "c1",
                    "title": "Rent Clause",
                    "original_text": "The rent is 10,000 INR per month.",
                    "plain_english": "You pay 10,000 per month.",
                    "plain_hindi": "किराया 10,000 प्रति माह है।",
                    "risk_level": "low",
                    "risk_score": 2,
                    "risk_reason": "Standard clause",
                    "clause_type": "payment",
                    "beneficial_to_user": True,
                }
            ],
        }

    def test_accepts_dict_directly(self):
        from services.ai_parser import parse_ai_response
        result = parse_ai_response(self._make_valid_raw())
        self.assertIn("summary", result)
        self.assertIn("clauses", result)
        self.assertGreater(len(result["clauses"]), 0)

    def test_accepts_valid_json_string(self):
        from services.ai_parser import parse_ai_response
        raw_str = json.dumps(self._make_valid_raw())
        result = parse_ai_response(raw_str)
        self.assertIn("clauses", result)

    def test_schema_validation_failure_raises(self):
        from services.ai_parser import parse_ai_response
        with self.assertRaises(ValueError):
            parse_ai_response({"summary": {}, "clauses": []})

    def test_invalid_type_raises_type_error(self):
        from services.ai_parser import parse_ai_response
        with self.assertRaises(TypeError):
            parse_ai_response(12345)  # type: ignore

    def test_recomputes_risk_counts(self):
        from services.ai_parser import parse_ai_response
        raw = self._make_valid_raw()
        raw["clauses"][0]["risk_level"] = "high"
        raw["summary"]["high_risk_count"] = 999  # Wrong — must be overwritten
        result = parse_ai_response(raw)
        self.assertEqual(result["summary"]["high_risk_count"], 1)

    def test_clause_id_auto_generated_when_missing(self):
        from services.ai_parser import parse_ai_response
        raw = self._make_valid_raw()
        del raw["clauses"][0]["id"]
        result = parse_ai_response(raw)
        self.assertTrue(result["clauses"][0]["id"].startswith("clause_"))


# ===========================================================================
# 4. Fake-success removal tests
# ===========================================================================

class TestFakeSuccessRemoved(unittest.IsolatedAsyncioTestCase):
    """
    Confirm that AIOrchestrator raises ProviderUnavailableError when all
    providers fail, instead of returning a fabricated JSON string.
    """

    async def test_raises_provider_unavailable_when_both_fail(self):
        from services.ai_provider import AIOrchestrator, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("Rate limited (429)"))
        orch.gemini.generate_completion = AsyncMock(side_effect=Exception("Gemini quota exceeded"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.gemini_api_key = "fake-key"
            with self.assertRaises(ProviderUnavailableError):
                await orch.generate_completion("Test prompt")

    async def test_raises_provider_unavailable_when_only_groq_fails_and_no_gemini(self):
        from services.ai_provider import AIOrchestrator, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("429 rate limit"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.gemini_api_key = ""  # No Gemini configured
            with self.assertRaises(ProviderUnavailableError):
                await orch.generate_completion("Test prompt")

    async def test_does_not_return_fake_json_string(self):
        """The old bug returned hard-coded JSON. Verify it is completely gone."""
        from services.ai_provider import AIOrchestrator, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_completion = AsyncMock(side_effect=Exception("rate_limit 429"))
        orch.gemini.generate_completion = AsyncMock(side_effect=Exception("Gemini down"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.gemini_api_key = "key"
            try:
                result = await orch.generate_completion("prompt")
                # If we reach here it returned something — fail if it's the old fake JSON
                self.assertNotIn("Standard terms and conditions", str(result))
                self.assertNotIn('"overall_risk": "LOW"', str(result))
                self.fail("Expected ProviderUnavailableError to be raised, got a result.")
            except ProviderUnavailableError:
                pass  # Correct behaviour

    async def test_chat_raises_provider_unavailable_when_both_fail(self):
        from services.ai_provider import AIOrchestrator, ProviderUnavailableError

        orch = AIOrchestrator()
        orch.groq.generate_chat_completion = AsyncMock(side_effect=Exception("Rate limited"))
        orch.gemini.generate_chat_completion = AsyncMock(side_effect=Exception("Gemini down"))

        with patch("services.ai_provider.settings") as mock_settings:
            mock_settings.gemini_api_key = "key"
            with self.assertRaises(ProviderUnavailableError):
                await orch.generate_chat_completion([{"role": "user", "content": "hello"}])


if __name__ == "__main__":
    unittest.main()
