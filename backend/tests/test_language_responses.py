"""Language (mr | hi | en) behaviour of AI responses, analysis translation, error catalog and KB overlays.
All AI calls are mocked; DB is the throwaway SQLite file from conftest."""

import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from database import get_db_ctx
from limiter import limiter
from services import kb_i18n, translation_service
from services.i18n_messages import translate_message
from services.lang import (
    ADVISOR_DISCLAIMER,
    CHAT_DISCLAIMER,
    CHAT_DISCLAIMER_EN,
    ensure_disclaimer,
    language_instruction,
    normalize_lang,
)

PW = "Str0ng-pass!"


@pytest.fixture(autouse=True)
def _fresh(client):
    client.cookies.clear()
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    client.cookies.clear()


def _register(client):
    email = f"lang_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": "L", "email": email, "password": PW})
    assert r.status_code == 201
    client.cookies.clear()
    return r.json()["access_token"], r.json()["user"]["id"]


def _h(token, lang=None):
    h = {"Authorization": f"Bearer {token}"}
    if lang:
        h["X-Lang"] = lang
    return h


ANALYSIS = {
    "status": "done",
    "document_id": "x",
    "summary": {
        "document_type": "Rental Agreement",
        "language": "English",
        "parties": ["Ramesh Patil", "Sita Kale"],
        "key_dates": [{"label": "Start date", "date": "2025-01-01"}],
        "overall_risk": "high",
        "risk_summary": "The landlord can terminate on short notice.",
        "high_risk_clauses": ["Termination"],
        "beneficial_clauses": ["Deposit refund"],
        "your_obligations": ["Pay rent by the 5th"],
        "other_party_rights": ["Inspect the flat"],
        "total_clauses": 2, "high_risk_count": 1, "medium_risk_count": 1, "low_risk_count": 0,
    },
    "clauses": [
        {"id": "c1", "title": "Termination", "original_text": "Landlord may terminate on 7 days notice.",
         "plain_english": "The landlord can end the lease with 7 days notice.", "plain_hindi": "मकान मालिक 7 दिन में समाप्त कर सकता है।",
         "risk_level": "high", "risk_score": 9, "risk_reason": "Very short notice.", "clause_type": "Termination",
         "beneficial_to_user": False, "page_number": 1},
        {"id": "c2", "title": "Deposit", "original_text": "Deposit refundable.",
         "plain_english": "Your deposit is returned.", "plain_hindi": "जमा वापस मिलेगा।",
         "risk_level": "medium", "risk_score": 4, "risk_reason": "Timeline unclear.", "clause_type": "Deposit",
         "beneficial_to_user": True, "page_number": 2},
    ],
    "metadata": {"total_chunks": 1},
}


def _seed(uid, doc_id=None, analysis=ANALYSIS):
    doc_id = doc_id or f"doc-lang-{uuid.uuid4().hex[:8]}"

    async def go():
        async with get_db_ctx() as db:
            await db.execute(
                "INSERT INTO documents (id, user_id, filename, file_url, file_size, document_type, file_hash, status, uploaded_at) "
                "VALUES ($1,$2,'f.pdf','local:///x',1,'',$3,'ready',$4)",
                doc_id, uid, uuid.uuid4().hex, datetime.utcnow().isoformat(),
            )
            await db.execute(
                "INSERT INTO analyses (id, document_id, result_json, analyzed_at) VALUES ($1,$2,$3,$4)",
                "an-" + doc_id, doc_id, json.dumps({**analysis, "document_id": doc_id}), datetime.utcnow().isoformat(),
            )
    asyncio.run(go())
    return doc_id


def _stored(doc_id):
    async def go():
        async with get_db_ctx() as db:
            row = await db.fetchrow("SELECT result_json FROM analyses WHERE document_id = $1", doc_id)
            return json.loads(row["result_json"])
    return asyncio.run(go())


# ── helpers ───────────────────────────────────────────────────────────────────

def test_normalize_lang():
    assert normalize_lang("mr") == "mr" and normalize_lang("HI") == "hi" and normalize_lang("mr-IN") == "mr"
    assert normalize_lang(None) == "en" and normalize_lang("fr") == "en" and normalize_lang("") == "en"


def test_language_instruction_names_language():
    assert "Marathi" in language_instruction("mr") and "Devanagari" in language_instruction("mr")
    assert "Hindi" in language_instruction("hi")
    assert "English" in language_instruction("en")


def test_ensure_disclaimer_localizes():
    out = ensure_disclaimer("उत्तर\n\n" + CHAT_DISCLAIMER_EN, "mr")
    assert CHAT_DISCLAIMER["mr"] in out and CHAT_DISCLAIMER_EN not in out
    assert CHAT_DISCLAIMER["hi"] in ensure_disclaimer("answer without note", "hi")
    assert ensure_disclaimer("x", "en") == "x"


# ── prompts ───────────────────────────────────────────────────────────────────

def test_chat_prompt_instructs_language_and_localizes_disclaimer():
    from services.groq_service import answer_question_about_document
    seen = {}

    async def fake(prompt, max_tokens=4000):
        seen["p"] = prompt
        return "उत्तर " + CHAT_DISCLAIMER_EN

    with patch("services.groq_service._call_groq", fake):
        out = asyncio.run(answer_question_about_document("doc text", "q?", lang="mr"))
    assert "Respond entirely in Marathi" in seen["p"]
    assert CHAT_DISCLAIMER["mr"] in seen["p"] and CHAT_DISCLAIMER_EN not in seen["p"]
    assert out.endswith(CHAT_DISCLAIMER["mr"])


def test_advisor_prompt_marathi_and_hindi():
    from services.groq_service import get_legal_advice
    for lang, word in (("mr", "Marathi"), ("hi", "Hindi")):
        captured = {}

        async def fake(messages, max_tokens=1800, temperature=0.2):
            captured["m"] = messages
            return "answer"

        with patch("services.groq_service._call_groq_chat", fake):
            out = asyncio.run(get_legal_advice("my question", [], lang=lang))
        assert f"Respond entirely in {word}" in captured["m"][0]["content"]
        assert f"Respond entirely in {word}" in captured["m"][-1]["content"]
        assert ADVISOR_DISCLAIMER[lang] in out


def test_insight_prompts_instruct_language():
    from services.groq_service import simulate_consequences, generate_negotiation
    prompts = []

    async def fake(prompt, max_tokens=4000):
        prompts.append(prompt)
        return json.dumps({"overview": "o", "scenarios": [], "summary": "s", "items": []})

    with patch("services.groq_service._call_groq", fake):
        asyncio.run(simulate_consequences("Rental", {}, [], lang="mr"))
        asyncio.run(generate_negotiation("Rental", {}, [], lang="hi"))
        asyncio.run(simulate_consequences("Rental", {}, [], lang="en"))
    assert "Respond entirely in Marathi" in prompts[0]
    assert "Respond entirely in Hindi" in prompts[1]
    assert "LANGUAGE (MANDATORY)" not in prompts[2]


# ── endpoints: chat / advisor pass lang through ─────────────────────────────────

def test_chat_endpoint_passes_header_lang(client):
    token, uid = _register(client)
    doc_id = _seed(uid)
    mock = AsyncMock(return_value="ok")
    with patch("routers.chat.get_doc_text", AsyncMock(return_value="text")), \
         patch("routers.chat.answer_question_about_document", mock):
        r = client.post("/api/v1/chat", json={"document_id": doc_id, "question": "q"}, headers=_h(token, "mr"))
        assert r.status_code == 200
        assert mock.call_args.kwargs["lang"] == "mr"
        r = client.post("/api/v1/chat", json={"document_id": doc_id, "question": "q", "lang": "hi"}, headers=_h(token, "mr"))
        assert mock.call_args.kwargs["lang"] == "hi"          # explicit body lang wins
        r = client.post("/api/v1/chat", json={"document_id": doc_id, "question": "q"}, headers=_h(token))
        assert mock.call_args.kwargs["lang"] == "en"          # default
        r = client.post("/api/v1/chat/multi", json={"document_ids": [doc_id], "question": "q"}, headers=_h(token, "hi"))
        assert r.status_code == 200 and mock.call_args.kwargs["lang"] == "hi"


def test_advisor_endpoint_passes_lang(client):
    token, _ = _register(client)
    mock = AsyncMock(return_value="ok")
    with patch("routers.advisor.get_legal_advice", mock):
        assert client.post("/api/v1/advisor", json={"message": "hi"}, headers=_h(token, "mr")).status_code == 200
    assert mock.call_args.kwargs["lang"] == "mr"


# ── insights cache separation ─────────────────────────────────────────────────

def test_insights_cache_is_per_language(client):
    token, uid = _register(client)
    doc_id = _seed(uid)
    mock = AsyncMock(side_effect=lambda *a, **k: {"overview": "text-" + k["lang"], "scenarios": []})
    with patch("routers.insights.simulate_consequences", mock):
        url = f"/api/v1/insights/{doc_id}/consequences"
        en = client.post(url, headers=_h(token)).json()
        mr = client.post(url, headers=_h(token, "mr")).json()
        assert en["consequences"]["overview"] == "text-en" and en["cached"] is False
        assert mr["consequences"]["overview"] == "text-mr" and mr["cached"] is False and mr["lang"] == "mr"
        assert mock.await_count == 2
        mr2 = client.post(url, headers=_h(token, "mr")).json()
        en2 = client.post(url, headers=_h(token)).json()
        assert mr2["cached"] is True and mr2["consequences"]["overview"] == "text-mr"
        assert en2["cached"] is True and en2["consequences"]["overview"] == "text-en"
        assert mock.await_count == 2


# ── translate endpoint ────────────────────────────────────────────────────────

def _fake_complete_factory(calls):
    async def fake(prompt, max_tokens):
        calls.append(prompt)
        payload = json.loads(prompt.split("JSON:\n", 1)[1])
        return json.dumps({k: "MR:" + v for k, v in payload.items()}, ensure_ascii=False)
    return fake


def test_translate_prompt_targets_language_and_batches():
    units = [(f"k{i}", "word " * 100) for i in range(10)]
    batches = translation_service.build_batches(units, 1800)
    assert len(batches) > 1 and sum(len(b) for b in batches) == 10
    p = translation_service._translate_prompt(batches[0], "mr")
    assert "Marathi" in p and "NEVER add, remove, change or invent" in p


def test_translate_endpoint_ownership_caching_and_schema(client):
    token, uid = _register(client)
    other_token, _ = _register(client)
    doc_id = _seed(uid)
    url = f"/api/v1/analyze/{doc_id}/translate"
    calls = []
    with patch("services.translation_service._complete", _fake_complete_factory(calls)):
        # ownership
        assert client.post(url, json={"lang": "mr"}, headers=_h(other_token)).status_code == 403
        assert client.post("/api/v1/analyze/nope/translate", json={"lang": "mr"}, headers=_h(token)).status_code == 404
        assert client.post(url, json={"lang": "mr"}).status_code == 401
        assert calls == []

        r = client.post(url, json={"lang": "mr"}, headers=_h(token))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["lang"] == "mr" and body["cached"] is False and body["partial"] is False
        a = body["analysis"]
        n_calls = len(calls)
        assert n_calls >= 1
        # same shape, translated text, untouched structure
        assert a["summary"]["risk_summary"] == "MR:The landlord can terminate on short notice."
        assert a["summary"]["document_type"] == "MR:Rental Agreement"
        assert a["summary"]["parties"] == ["Ramesh Patil", "Sita Kale"]
        assert a["summary"]["key_dates"] == [{"label": "MR:Start date", "date": "2025-01-01"}]
        assert a["summary"]["your_obligations"] == ["MR:Pay rent by the 5th"]
        c1 = a["clauses"][0]
        assert c1["plain_english"].startswith("MR:") and c1["risk_reason"].startswith("MR:")
        assert c1["original_text"] == ANALYSIS["clauses"][0]["original_text"]
        assert c1["risk_level"] == "high" and c1["risk_score"] == 9 and c1["id"] == "c1"
        assert a["summary"]["total_clauses"] == 2 and a["summary"]["high_risk_count"] == 1
        from services.analysis_schema import validate_analysis
        validate_analysis(a)  # still a valid analysis

        # cached inside result_json["translations"]["mr"]
        stored = _stored(doc_id)
        assert "patch" in stored["translations"]["mr"]
        assert stored["clauses"][0]["plain_english"] == ANALYSIS["clauses"][0]["plain_english"]  # base untouched

        # second request is instant: no new AI calls
        r2 = client.post(url, json={"lang": "mr"}, headers=_h(token))
        assert r2.json()["cached"] is True and len(calls) == n_calls
        assert r2.json()["analysis"]["clauses"][1]["plain_english"].startswith("MR:")

        # header/query lang also work; english returns the base without AI
        assert client.post(url + "?lang=mr", headers=_h(token)).json()["cached"] is True
        en = client.post(url, json={"lang": "en"}, headers=_h(token)).json()
        assert en["analysis"]["clauses"][0]["plain_english"] == ANALYSIS["clauses"][0]["plain_english"]
        assert len(calls) == n_calls

        # status endpoint: base by default (with translations), translated view with ?lang=mr
        s = client.get(f"/api/v1/analyze/{doc_id}/status", headers=_h(token)).json()
        assert s["analysis"]["clauses"][0]["plain_english"] == ANALYSIS["clauses"][0]["plain_english"]
        assert "mr" in s["analysis"]["translations"]
        s = client.get(f"/api/v1/analyze/{doc_id}/status?lang=mr", headers=_h(token)).json()
        assert s["analysis"]["clauses"][0]["plain_english"].startswith("MR:") and s["analysis"]["view_lang"] == "mr"
        s = client.get(f"/api/v1/analyze/{doc_id}/status?lang=hi", headers=_h(token)).json()
        assert s["analysis"]["clauses"][0]["plain_english"] == ANALYSIS["clauses"][0]["plain_english"]


def test_translate_hindi_also_sets_plain_hindi(client):
    token, uid = _register(client)
    doc_id = _seed(uid)
    calls = []
    with patch("services.translation_service._complete", _fake_complete_factory(calls)):
        a = client.post(f"/api/v1/analyze/{doc_id}/translate", json={"lang": "hi"}, headers=_h(token)).json()["analysis"]
    assert a["clauses"][0]["plain_hindi"] == a["clauses"][0]["plain_english"] and a["clauses"][0]["plain_hindi"].startswith("MR:")


def test_translate_failure_is_502_and_not_cached(client):
    token, uid = _register(client)
    doc_id = _seed(uid)
    with patch("services.translation_service._complete", AsyncMock(side_effect=RuntimeError("secret-provider-detail"))):
        r = client.post(f"/api/v1/analyze/{doc_id}/translate", json={"lang": "mr"}, headers=_h(token))
    assert r.status_code == 502 and "secret-provider-detail" not in r.text
    assert "translations" not in _stored(doc_id)


def test_translate_partial_is_not_cached(client):
    token, uid = _register(client)
    doc_id = _seed(uid)

    async def drops_one(prompt, max_tokens):
        payload = json.loads(prompt.split("JSON:\n", 1)[1])
        keys = list(payload)
        return json.dumps({k: "MR:" + payload[k] for k in keys[1:]}, ensure_ascii=False)  # always omits t0

    with patch("services.translation_service._complete", drops_one):
        r = client.post(f"/api/v1/analyze/{doc_id}/translate", json={"lang": "mr"}, headers=_h(token))
    assert r.status_code == 200 and r.json()["partial"] is True
    assert "translations" not in _stored(doc_id)


def test_translate_requires_finished_analysis(client):
    token, uid = _register(client)
    doc_id = _seed(uid, analysis={"status": "processing"})
    r = client.post(f"/api/v1/analyze/{doc_id}/translate", json={"lang": "mr"}, headers=_h(token))
    assert r.status_code == 400


# ── error catalog ─────────────────────────────────────────────────────────────

def test_error_detail_translated_via_x_lang(client):
    r_en = client.get("/api/v1/upload/history")
    assert r_en.status_code in (401,)
    en = r_en.json()["detail"]
    mr = client.get("/api/v1/upload/history", headers={"X-Lang": "mr"}).json()["detail"]
    hi = client.get("/api/v1/upload/history", headers={"X-Lang": "hi"}).json()["detail"]
    assert mr != en and hi != en and mr != hi
    assert any("ऀ" <= ch <= "ॿ" for ch in mr)
    # invalid lang -> English
    assert client.get("/api/v1/upload/history", headers={"X-Lang": "xx"}).json()["detail"] == en


def test_error_ownership_message_localized(client):
    token, uid = _register(client)
    other, _ = _register(client)
    doc_id = _seed(uid)
    r = client.get(f"/api/v1/analyze/{doc_id}/status", headers=_h(other, "mr"))
    assert r.status_code == 403
    assert r.json()["detail"] == translate_message("You do not have permission to access this document.", "mr")
    assert r.json()["detail"] != "You do not have permission to access this document."


def test_unknown_error_strings_pass_through():
    assert translate_message("Some brand new error 123", "mr") == "Some brand new error 123"
    assert translate_message("Some brand new error 123", "hi") == "Some brand new error 123"
    assert translate_message(["not", "a", "string"], "mr") == ["not", "a", "string"]
    assert translate_message("Document not found.", "en") == "Document not found."


def test_dynamic_error_patterns():
    assert "25" in translate_message("File too large. Maximum allowed size is 25 MB.", "mr")
    assert "50" in translate_message("Document exceeds the maximum limit of 50 pages. Please upload a shorter document or excerpt.", "hi")
    assert translate_message("Age requirement is between 18 and 60 years (Your age: 70)", "mr").count("70") == 1


def test_every_catalog_entry_has_hi_and_mr():
    from services.i18n_messages import MESSAGES, PATTERNS
    for en, t in MESSAGES.items():
        assert t.get("hi") and t.get("mr"), en
    for _, t in PATTERNS:
        assert t.get("hi") and t.get("mr")


def test_all_router_detail_strings_are_cataloged():
    """Every static HTTPException detail in routers/services/auth_google must be in the catalog."""
    import ast
    import os
    from services.i18n_messages import MESSAGES

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing = []
    files = [os.path.join(root, "auth_google.py")]
    for d in ("routers", "services"):
        files += [os.path.join(root, d, f) for f in os.listdir(os.path.join(root, d)) if f.endswith(".py")]
    for path in files:
        if "whatsapp" in path:
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "HTTPException":
                for kw in node.keywords:
                    if kw.arg == "detail":
                        v = kw.value
                        if isinstance(v, ast.Constant) and isinstance(v.value, str):
                            if v.value not in MESSAGES:
                                missing.append((os.path.basename(path), v.value))
                        elif isinstance(v, ast.JoinedStr):
                            pass  # f-strings are covered by PATTERNS
    assert not missing, missing


# ── KB overlay mechanism ─────────────────────────────────────────────────────

def test_kb_localize_overlay_sibling_and_translations(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_i18n, "OVERLAY_DIR", str(tmp_path))
    kb_i18n._load_overlay_cached.cache_clear()
    rec = {
        "display_name": "Aadhaar Card", "icon": "X", "official_portal": "https://uidai.gov.in",
        "overview": "English overview", "overview_mr": "sibling mr",
        "services": [{"service": "New Enrolment", "description": "desc", "documents_required": ["Proof A", "Proof B"],
                      "translations": {"mr": {"description": "record mr"}}}],
    }
    (tmp_path / "legal_id.mr.json").write_text(json.dumps({
        "aadhaar.display_name": "आधार कार्ड",
        "aadhaar.services.0.service": "नवीन नोंदणी",
        "aadhaar.services.0.documents_required.1": "पुरावा ब",
    }, ensure_ascii=False), encoding="utf-8")

    out = kb_i18n.localize(rec, "legal_id", "mr", root="aadhaar")
    assert out["display_name"] == "आधार कार्ड"
    assert out["overview"] == "sibling mr" and "overview_mr" not in out
    svc = out["services"][0]
    assert svc["service"] == "New Enrolment" and svc["service_display"] == "नवीन नोंदणी"   # id kept
    assert svc["description"] == "record mr"
    assert svc["documents_required"] == ["Proof A", "पुरावा ब"]                           # partial overlay falls back
    assert out["official_portal"] == "https://uidai.gov.in" and out["icon"] == "X"
    # no overlay for hi -> English
    assert kb_i18n.localize(rec, "legal_id", "hi", root="aadhaar")["display_name"] == "Aadhaar Card"
    assert kb_i18n.localize(rec, "legal_id", "en", root="aadhaar") is rec


def test_hub_endpoints_accept_lang_with_english_fallback(client, tmp_path, monkeypatch):
    base = client.get("/api/v1/legal-id/aadhaar").json()["guidance"]
    monkeypatch.setattr(kb_i18n, "OVERLAY_DIR", str(tmp_path))
    kb_i18n._load_overlay_cached.cache_clear()
    # no overlay file: English fallback, lang echoed
    r = client.get("/api/v1/legal-id/aadhaar", headers={"X-Lang": "mr"}).json()
    assert r["guidance"] == base and r["lang"] == "mr"
    (tmp_path / "legal_id.mr.json").write_text(json.dumps({"aadhaar.display_name": "आधार कार्ड"}, ensure_ascii=False), encoding="utf-8")
    r = client.get("/api/v1/legal-id/aadhaar?lang=mr").json()
    assert r["guidance"]["display_name"] == "आधार कार्ड" and r["guidance"]["overview"] == base["overview"]
    lst = client.get("/api/v1/legal-id/", headers={"X-Lang": "mr"}).json()
    assert [t for t in lst["id_types"] if t["key"] == "aadhaar"][0]["display_name"] == "आधार कार्ड"
    assert client.get("/api/v1/property/", headers={"X-Lang": "hi"}).json()["lang"] == "hi"
    assert client.get("/api/v1/business/", headers={"X-Lang": "hi"}).json()["lang"] == "hi"


def test_localized_checklist_seed(tmp_path, monkeypatch):
    from services.legal_id_kb import get_id_guidance
    monkeypatch.setattr(kb_i18n, "OVERLAY_DIR", str(tmp_path))
    kb_i18n._load_overlay_cached.cache_clear()
    g = get_id_guidance("aadhaar")
    svc = g["services"][0]["service"]
    (tmp_path / "legal_id.mr.json").write_text(json.dumps({"aadhaar.services.0.documents_required.0": "पुरावा १"}, ensure_ascii=False), encoding="utf-8")
    items = kb_i18n.localized_checklist(g, "aadhaar", "legal_id", svc, "mr")
    assert items[0] == "पुरावा १" and items[1:] == g["services"][0]["documents_required"][1:]
    assert kb_i18n.localized_checklist(g, "aadhaar", "legal_id", "no such service", "mr") is None


def test_yojana_gap_analysis_localized():
    from routers.yojana import SchemeMatchRequest, evaluate_scheme_eligibility
    scheme = {"eligibility": {"income_max": 100000, "requires_landholding": True}}
    gaps = evaluate_scheme_eligibility(scheme, SchemeMatchRequest(annual_income=500000))["gap_analysis"]
    mr = [translate_message(g, "mr") for g in gaps]
    assert all(m != g for m, g in zip(mr, gaps))
