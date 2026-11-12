"""
test_provider_fixes.py — Regression tests for provider error classification,
response normalization, budget manager header expiry, and JSON repair.

All unit tests use mocked provider responses with zero live API or network calls.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.chunking_service import classify_chunk_error, is_retryable_error
from services.gemini_service import _extract_json
from services.groq_service import (
    _call_gemini_rest,
    _fallback_to_gemini,
    _normalize_clause_payload,
    GeminiPermanentError,
    GeminiRateLimitError,
)
from services.provider_budget_manager import ProductionProviderBudgetManager
from services.model_capabilities import ModelCapability


# ---------------------------------------------------------------------------
# 1. Gemini REST fallback error classification & project denial tests
# ---------------------------------------------------------------------------

class TestGeminiRestFallback:
    """Unit tests for _call_gemini_rest error classification."""

    def _make_response(self, status_code: int, body: dict | str) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        if isinstance(body, dict):
            resp.json.return_value = body
            resp.text = json.dumps(body)[:200]
        else:
            resp.json.side_effect = ValueError("not json")
            resp.text = str(body)[:200]
        return resp

    def test_403_raises_permanent_error_and_flags_unavailable(self):
        async def run():
            import services.groq_service as gs
            gs._gemini_permanently_unavailable = False

            body = {"error": {"code": 403, "message": "Your project has been denied access.", "status": "PERMISSION_DENIED"}}
            fake_resp = self._make_response(403, body)
            with patch("httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=fake_resp)
                mock_cls.return_value = mock_client
                with pytest.raises(GeminiPermanentError, match="403"):
                    await _call_gemini_rest("gemini-test", "test prompt", 100, "fake-key")

            assert gs._gemini_permanently_unavailable is True
        asyncio.run(run())

    def test_401_raises_permanent_error(self):
        async def run():
            import services.groq_service as gs
            gs._gemini_permanently_unavailable = False

            fake_resp = self._make_response(401, {"error": {"message": "API_KEY_INVALID"}})
            with patch("httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=fake_resp)
                mock_cls.return_value = mock_client
                with pytest.raises(GeminiPermanentError, match="401"):
                    await _call_gemini_rest("gemini-test", "test prompt", 100, "fake-key")
        asyncio.run(run())

    def test_429_raises_rate_limit_error(self):
        async def run():
            fake_resp = self._make_response(429, "rate limited")
            with patch("httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=fake_resp)
                mock_cls.return_value = mock_client
                with pytest.raises(GeminiRateLimitError):
                    await _call_gemini_rest("gemini-test", "test prompt", 100, "fake-key")
        asyncio.run(run())

    def test_200_returns_text(self):
        async def run():
            body = {"candidates": [{"content": {"parts": [{"text": "Extracted legal clause content."}]}}]}
            fake_resp = self._make_response(200, body)
            with patch("httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=fake_resp)
                mock_cls.return_value = mock_client
                result = await _call_gemini_rest("gemini-2.5-flash", "test", 100, "fake-key")
                assert result == "Extracted legal clause content."
        asyncio.run(run())

    def test_fallback_skips_when_permanently_unavailable(self):
        async def run():
            import services.groq_service as gs
            gs._gemini_permanently_unavailable = True

            with patch("services.groq_service.settings") as mock_settings:
                mock_settings.gemini_api_key = "fake-key"
                with pytest.raises(GeminiPermanentError, match="skipped"):
                    await _fallback_to_gemini("test prompt")
        asyncio.run(run())


# ---------------------------------------------------------------------------
# 2. Response normalization tests
# ---------------------------------------------------------------------------

class TestNormalizeClausePayload:
    """Unit tests for _normalize_clause_payload."""

    def test_bare_list_passthrough(self):
        payload = [{"title": "Notice Period", "original_text": "30 days notice"}]
        result = _normalize_clause_payload(payload)
        assert result == payload

    def test_dict_with_clauses_key(self):
        payload = {"clauses": [{"title": "Rent", "original_text": "Rent is 10k"}]}
        result = _normalize_clause_payload(payload)
        assert result == [{"title": "Rent", "original_text": "Rent is 10k"}]

    def test_dict_with_sections_key(self):
        payload = {"sections": [{"title": "Jurisdiction", "original_text": "Courts in Pune"}]}
        result = _normalize_clause_payload(payload)
        assert result == [{"title": "Jurisdiction", "original_text": "Courts in Pune"}]

    def test_dict_with_items_key(self):
        payload = {"items": [{"title": "Deposit", "original_text": "50000"}]}
        result = _normalize_clause_payload(payload)
        assert result == [{"title": "Deposit", "original_text": "50000"}]

    def test_single_clause_dict_wrapping(self):
        payload = {"title": "Arbitration", "original_text": "Arbitration under ICA 1996"}
        result = _normalize_clause_payload(payload)
        assert result == [payload]

    def test_string_clauses_converted_to_dicts(self):
        payload = ["The tenant shall pay 10000 rent.", "The deposit is 50000."]
        result = _normalize_clause_payload(payload)
        assert len(result) == 2
        assert result[0]["original_text"] == "The tenant shall pay 10000 rent."
        assert result[1]["original_text"] == "The deposit is 50000."

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError, match="no usable clauses"):
            _normalize_clause_payload([])

    def test_arbitrary_dict_without_clauses_raises(self):
        with pytest.raises(ValueError, match="AI returned a JSON object without a clause array"):
            _normalize_clause_payload({"summary": "This is a document", "notes": "No clauses here"})

    def test_invalid_type_raises_value_error(self):
        with pytest.raises(ValueError, match="must be an array or wrapped object"):
            _normalize_clause_payload(99999)


# ---------------------------------------------------------------------------
# 3. Budget manager header expiry tests
# ---------------------------------------------------------------------------

class TestBudgetManagerHeaderExpiry:
    """Verify header constraints expire and do not cause permanent deadlocks."""

    def test_expired_header_state_clears_automatically(self):
        async def run():
            mgr = ProductionProviderBudgetManager(default_cooloff_seconds=15.0)
            cap = ModelCapability(
                name="test-model",
                provider="groq",
                context_window=128000,
                max_output_tokens=16384,
                modalities=["text"],
                vision_support=False,
                structured_output="json_schema",
            )

            # Record a success with remaining tokens = 0, reset in 0.05 second
            headers = {
                "x-ratelimit-remaining-tokens": "0",
                "x-ratelimit-reset-tokens": "0.05s",
            }
            await mgr.record_success("groq", "test-model", 500, headers=headers)

            # Immediately after, 0 tokens remaining should return False
            assert await mgr.can_send(1000, cap) is False

            # After waiting past reset duration (0.1s), constraint should expire
            await asyncio.sleep(0.1)
            assert await mgr.can_send(1000, cap) is True
        asyncio.run(run())


# ---------------------------------------------------------------------------
# 4. Error classification tests
# ---------------------------------------------------------------------------

class TestErrorClassification:
    """Verify chunk errors are accurately classified."""

    def test_groq_rate_limited_message_is_rate_limit(self):
        exc = RuntimeError("Groq is currently rate-limited or in cooloff (11.0s remaining).")
        assert classify_chunk_error(exc) == "rate_limit"
        assert is_retryable_error("rate_limit") is True

    def test_hyphenated_rate_limit_is_rate_limit(self):
        exc = Exception("rate-limit exceeded on provider")
        assert classify_chunk_error(exc) == "rate_limit"

    def test_cooloff_is_rate_limit(self):
        exc = Exception("cooloff in progress for 30s")
        assert classify_chunk_error(exc) == "rate_limit"

    def test_http_429_is_rate_limit(self):
        exc = Exception("HTTP 429 Too Many Requests")
        assert classify_chunk_error(exc) == "rate_limit"

    def test_timeout_is_transient(self):
        exc = asyncio.TimeoutError("request timed out")
        assert classify_chunk_error(exc) == "transient"
        assert is_retryable_error("transient") is True

    def test_json_error_is_malformed_response(self):
        exc = ValueError("No valid JSON found in response: ...")
        assert classify_chunk_error(exc) == "malformed_response"
        assert is_retryable_error("malformed_response") is True

    def test_403_is_permanent(self):
        exc = Exception("HTTP 403 Forbidden")
        assert classify_chunk_error(exc) == "permanent"
        assert is_retryable_error("permanent") is False


# ---------------------------------------------------------------------------
# 5. Truncated JSON repair tests
# ---------------------------------------------------------------------------

class TestJsonRepair:
    """Verify defensive repair of truncated JSON arrays."""

    def test_clean_json_array(self):
        raw = '[{"id": "clause_1", "title": "Rent"}]'
        parsed = _extract_json(raw)
        assert isinstance(parsed, list)
        assert parsed[0]["title"] == "Rent"

    def test_truncated_json_array_repair(self):
        raw = '[{"id": "clause_1", "title": "Rent"}, {"id": "clause_2", "title": "Deposit"}, {"id": "clause_3", "tit'
        parsed = _extract_json(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["title"] == "Rent"
        assert parsed[1]["title"] == "Deposit"


# ---------------------------------------------------------------------------
# 6. Worker imports test
# ---------------------------------------------------------------------------

class TestWorkerImports:
    def test_worker_imports_without_name_error(self):
        import sys
        if "worker" in sys.modules:
            del sys.modules["worker"]
        import worker
        assert hasattr(worker, "enqueue_analysis")
        assert hasattr(worker, "WorkerSettings")
