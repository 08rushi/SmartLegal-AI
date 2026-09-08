import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from routers.auth import create_access_token


@pytest.fixture(scope="session", autouse=True)
def mock_db_pool():
    """Mock database pool on FastAPI app state."""
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.fetch = AsyncMock(return_value=[])
    mock_pool.execute = AsyncMock(return_value=None)
    app.state.pool = mock_pool
    yield mock_pool


@pytest.fixture(autouse=True)
def mock_ai_provider_hermetic(monkeypatch):
    """
    Ensure all unit tests execute hermetically and deterministically offline
    without requiring external Groq/Gemini API keys, avoiding CI network failures
    and provider rate limits.
    """
    import json
    from services.ai_provider import ai_orchestrator

    async def fake_generate_completion(prompt: str, max_tokens: int = 4000) -> str:
        prompt_lower = prompt.lower()

        # 1. Intent Classification Prompt
        if "intent classifier for smartlegal ai" in prompt_lower:
            msg = ""
            if 'user message: "' in prompt_lower:
                try:
                    start = prompt_lower.index('user message: "') + len('user message: "')
                    end = prompt_lower.index('"', start)
                    msg = prompt_lower[start:end]
                except Exception:
                    msg = prompt_lower
            else:
                msg = prompt_lower

            has_media = "has attached media file: true" in prompt_lower or "has_media: true" in prompt_lower

            if "notice period" in msg or "termination clause" in msg or "in this agreement" in msg or "in this contract" in msg:
                intent = "document_analysis"
            elif any(w in msg for w in ("legal notice", "लीगल नोटिस", "court notice", "lawyer notice")) or ("notice" in msg and "period" not in msg and "agreement" not in msg):
                intent = "legal_notice"
            elif has_media or any(w in msg for w in ("contract", "agreement", "analyze", "कागदपत्र", "करार", "pdf", "photo", "image", "document", "एग्रीमेंट", "दस्तावेज़")):
                intent = "document_analysis"
            elif any(w in msg for w in ("draft", "मसुदा", "ड्राफ्ट", "तयार करा", "बनाएं")):
                intent = "document_drafting"
            elif any(w in msg for w in ("matter", "case", "status", "माझे अर्ज", "मेरे मामले")):
                intent = "my_matters"
            elif any(w in msg for w in ("menu", "help", "मदत", "मेनू")):
                intent = "help_menu"
            elif any(w in msg for w in ("language", "भाषा")):
                intent = "language_change"
            elif any(w in msg for w in ("random", "xyz", "asdf")):
                intent = "unknown"
            else:
                intent = "legal_question"

            return json.dumps({"intent": intent, "confidence": 0.95})

        # 2. Document Analysis / Summary Prompt
        if "document analysis" in prompt_lower or "overall_risk" in prompt_lower or "summary" in prompt_lower:
            return json.dumps({
                "summary": {
                    "document_type": "Rental Agreement",
                    "overall_risk": "LOW",
                    "key_provisions": ["11 months lease duration", "Security deposit refund in 30 days"],
                    "high_risk_clauses": []
                }
            })

        # 3. Default text completion
        return "SmartLegal AI Legal Guidance: Under Indian Law, rights and obligations are governed by applicable statutes."

    async def fake_generate_chat_completion(messages: list, max_tokens: int = 1800) -> str:
        all_content = " ".join(m.get("content", "") for m in messages)
        all_content_lower = all_content.lower()

        # Check for specific document follow-up queries
        if "notice period" in all_content_lower or "clause 4" in all_content_lower:
            return "The notice period specified in Clause 4 is 30 days written notice."

        if "strictly in marathi" in all_content_lower or "language: marathi" in all_content_lower:
            return (
                "कायदेशीर सल्ला: भारतीय कायद्यानुसार ही कायदेशीर नोटीस आणि करार आहे. भाडे करार आणि भारतीय पुरावा कायद्यानुसार आपल्या हक्कांचे रक्षण केले जाते.\n\n"
                "📌 *टीप: हा भारतीय कायद्यावर आधारित एआय सल्ला आहे, परवानाधारक वकीलाचा पर्याय नाही.*"
            )
        elif "strictly in hindi" in all_content_lower or "language: hindi" in all_content_lower:
            return (
                "कानूनी मार्गदर्शन: भारतीय कानून के तहत आपके दस्तावेज़ और एग्रीमेंट की समीक्षा की गई है। भारतीय अनुबंध अधिनियम 1872 के तहत अधिकार सुरक्षित हैं।\n\n"
                "📌 *नोट: यह भारतीय कानून पर आधारित एआई मार्गदर्शन है, किसी वकील का विकल्प नहीं है।*"
            )

        return (
            "Legal Guidance: Under Indian Law (Indian Contract Act 1872 / Advocates Act 1961), tenant and landlord rights are governed by local Rent Control Acts. This legal advice covers your rights and agreement terms.\n\n"
            "📌 *Note: This is AI legal guidance based on Indian law, not a substitute for a licensed advocate.*"
        )

    monkeypatch.setattr(ai_orchestrator, "generate_completion", fake_generate_completion)
    monkeypatch.setattr(ai_orchestrator, "generate_chat_completion", fake_generate_chat_completion)
    yield


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client



@pytest.fixture
def user_a_token():
    """Valid JWT token for User A."""
    return create_access_token("user_a_id_12345", 0)


@pytest.fixture
def user_b_token():
    """Valid JWT token for User B."""
    return create_access_token("user_b_id_67890", 0)


@pytest.fixture
def auth_headers_user_a(user_a_token):
    return {"Authorization": f"Bearer {user_a_token}"}


@pytest.fixture
def auth_headers_user_b(user_b_token):
    return {"Authorization": f"Bearer {user_b_token}"}

