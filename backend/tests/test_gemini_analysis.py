"""Tests for services/gemini_analysis.py (all network calls mocked — Gemini is never contacted)."""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from services import gemini_analysis as ga

LONG_TEXT = "[Page 1]\n" + ("The tenant shall pay rent on the first day of each month without set-off. " * 450)
SHORT_TEXT = "[Page 1]\nThe tenant shall pay rent monthly."

CLAUSES = [
    {"id": "clause_1", "title": "Rent", "original_text": "pay rent", "plain_english": "Pay monthly.",
     "plain_hindi": "मासिक किराया दें।", "risk_level": "high", "risk_score": 8, "risk_reason": "No set-off",
     "clause_type": "Rent", "beneficial_to_user": False},
    {"id": "clause_2", "title": "Notice", "original_text": "notice", "plain_english": "30 days.",
     "risk_level": "weird-level", "risk_score": "x", "risk_reason": "", "clause_type": "Notice"},
]


def _fake_call_json(prompt: str, max_out: int = 0) -> str:
    if "Identify exactly what this document is" in prompt:
        return json.dumps({"document_type": "Rental Agreement", "category": "agreement", "acts": ["Transfer of Property Act 1882"]})
    if "write a summary" in prompt:
        return json.dumps({"document_type": "Rental Agreement", "language": "English", "parties": ["Landlord", "Tenant"],
                           "key_dates": [], "overall_risk": "high", "risk_summary": "One-sided.", "high_risk_clauses": ["Rent"],
                           "beneficial_clauses": [], "your_obligations": [], "other_party_rights": []})
    return json.dumps({"clauses": CLAUSES})  # wrapped shape must be normalised


class TestTryGeminiAnalysis(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        ga.reset_availability()

    def tearDown(self):
        ga.reset_availability()

    async def test_returns_none_when_provider_is_groq(self):
        with patch.object(ga.settings, "analysis_provider", "groq"), patch.object(ga.settings, "gemini_api_key", "k"):
            self.assertIsNone(await ga.try_gemini_analysis(LONG_TEXT, "a.pdf"))

    async def test_returns_none_without_api_key(self):
        with patch.object(ga.settings, "analysis_provider", "auto"), patch.object(ga.settings, "gemini_api_key", ""):
            self.assertIsNone(await ga.try_gemini_analysis(LONG_TEXT, "a.pdf"))

    async def test_auto_mode_keeps_short_documents_on_groq(self):
        with patch.object(ga.settings, "analysis_provider", "auto"), patch.object(ga.settings, "gemini_api_key", "k"), \
             patch.object(ga, "_call_json", new=AsyncMock(side_effect=AssertionError("must not call Gemini"))):
            self.assertIsNone(await ga.try_gemini_analysis(SHORT_TEXT, "a.pdf"))

    async def test_full_analysis_shape_and_normalisation(self):
        with patch.object(ga.settings, "analysis_provider", "auto"), patch.object(ga.settings, "gemini_api_key", "k"), \
             patch.object(ga, "_call_json", new=AsyncMock(side_effect=_fake_call_json)):
            result = await ga.try_gemini_analysis(LONG_TEXT, "rent.pdf")
        self.assertIsNotNone(result)
        self.assertEqual(len(result["clauses"]), len(CLAUSES) * result["metadata"]["total_chunks"])
        self.assertEqual(result["summary"]["total_clauses"], len(result["clauses"]))
        self.assertEqual(result["summary"]["overall_risk"], "high")
        self.assertEqual(result["metadata"]["analysis_engine"], "gemini")
        self.assertEqual(result["metadata"]["completion_ratio"], 1.0)
        c2 = next(c for c in result["clauses"] if c["id"] == "clause_2")
        self.assertEqual(c2["risk_level"], "medium")   # invalid level normalised
        self.assertEqual(c2["risk_score"], 5)          # invalid score normalised
        self.assertIn("page_number", c2)

    async def test_falls_back_to_none_when_gemini_refuses_access(self):
        with patch.object(ga.settings, "analysis_provider", "gemini"), patch.object(ga.settings, "gemini_api_key", "k"), \
             patch.object(ga, "_call_json", new=AsyncMock(side_effect=ga.GeminiUnavailable("403"))):
            self.assertIsNone(await ga.try_gemini_analysis(LONG_TEXT, "a.pdf"))

    async def test_falls_back_to_none_on_unexpected_failure(self):
        with patch.object(ga.settings, "analysis_provider", "gemini"), patch.object(ga.settings, "gemini_api_key", "k"), \
             patch.object(ga, "_call_json", new=AsyncMock(side_effect=RuntimeError("boom"))), \
             patch("services.chunking_service.asyncio.sleep", new=AsyncMock()):
            self.assertIsNone(await ga.try_gemini_analysis(LONG_TEXT, "a.pdf"))


class TestCallJson(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        ga.reset_availability()

    def tearDown(self):
        ga.reset_availability()

    def _mock_client(self, status: int, body: dict):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status
        resp.json.return_value = body
        resp.text = json.dumps(body)
        client = MagicMock()
        client.post = AsyncMock(return_value=resp)
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=client)
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm, client

    async def test_403_marks_unavailable_and_raises(self):
        cm, _ = self._mock_client(403, {"error": {"message": "free tier is not available for this project"}})
        with patch.object(ga.settings, "gemini_api_key", "k"), patch("services.gemini_analysis.httpx.AsyncClient", return_value=cm):
            with self.assertRaises(ga.GeminiUnavailable):
                await ga._call_json("hi")
            self.assertFalse(ga.is_usable())   # not retried for a while

    async def test_success_returns_text_and_disables_thinking_for_25_flash(self):
        body = {"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}, "finishReason": "STOP"}]}
        cm, client = self._mock_client(200, body)
        with patch.object(ga.settings, "gemini_api_key", "k"), patch.object(ga.settings, "gemini_text_model", "gemini-2.5-flash"), \
             patch("services.gemini_analysis.httpx.AsyncClient", return_value=cm):
            out = await ga._call_json("hi", max_out=100)
        self.assertEqual(out, '{"ok": true}')
        sent = client.post.call_args.kwargs["json"]["generationConfig"]
        self.assertEqual(sent["thinkingConfig"], {"thinkingBudget": 0})
        self.assertEqual(sent["responseMimeType"], "application/json")

    async def test_429_is_classified_as_rate_limit_for_retry(self):
        from services.chunking_service import classify_chunk_error
        cm, _ = self._mock_client(429, {})
        with patch.object(ga.settings, "gemini_api_key", "k"), patch("services.gemini_analysis.httpx.AsyncClient", return_value=cm):
            with self.assertRaises(RuntimeError) as ctx:
                await ga._call_json("hi")
        self.assertEqual(classify_chunk_error(ctx.exception), "rate_limit")


if __name__ == "__main__":
    unittest.main()
