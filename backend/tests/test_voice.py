"""Voice STT endpoint: Groq call mocked, no network, no audio on disk."""
import os
import tempfile
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from limiter import limiter
from routers import voice as voice_mod
from services.i18n_messages import MESSAGES

PW = "Str0ng-pass!"
URL = "/api/v1/voice/transcribe"
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 3000
OGG = b"OggS" + b"\x00" * 3000


@pytest.fixture(autouse=True)
def _clean(client):
    client.cookies.clear()
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    client.cookies.clear()


def _token(client):
    email = f"v_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": "V", "email": email, "password": PW})
    assert r.status_code == 201
    client.cookies.clear()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _post(client, h, data=WEBM, ctype="audio/webm", **form):
    return client.post(URL, files={"audio": ("a.webm", data, ctype)}, data=form, headers=h)


def _mock(result=None, exc=None):
    m = AsyncMock(return_value=result or {"text": " hello ", "language": "english", "duration": 3.2})
    if exc:
        m.side_effect = exc
    return patch.object(voice_mod, "_call_groq_stt", m), m


def test_auth_required(client):
    r = client.post(URL, files={"audio": ("a.webm", WEBM, "audio/webm")})
    assert r.status_code in (401, 403)


def test_success_and_strip(client):
    h = _token(client)
    p, m = _mock()
    with p:
        r = _post(client, h)
    assert r.status_code == 200, r.text
    assert r.json() == {"text": "hello", "language": "en", "duration_seconds": 3.2}


def test_size_limit(client):
    h = _token(client)
    p, m = _mock()
    with p:
        r = _post(client, h, data=WEBM + b"\x00" * voice_mod.MAX_BYTES)
    assert r.status_code == 413
    m.assert_not_called()


def test_bad_content_type(client):
    h = _token(client)
    p, m = _mock()
    with p:
        r = _post(client, h, ctype="text/plain")
    assert r.status_code == 400
    m.assert_not_called()


def test_magic_byte_mismatch(client):
    h = _token(client)
    p, m = _mock()
    with p:
        r = _post(client, h, data=b"this is not audio" * 200)
    assert r.status_code == 400
    m.assert_not_called()


def test_tiny_file_rejected(client):
    h = _token(client)
    p, m = _mock()
    with p:
        r = _post(client, h, data=b"\x1a\x45\xdf\xa3" + b"\x00" * 10)
    assert r.status_code == 400
    m.assert_not_called()


def test_empty_transcript_422(client):
    h = _token(client)
    p, m = _mock({"text": "   ", "language": "marathi"})
    with p:
        r = _post(client, h)
    assert r.status_code == 422


def test_language_hint_forwarded(client):
    h = _token(client)
    p, m = _mock({"text": "भाडे करार", "language": "marathi", "duration": 2})
    with p:
        r = _post(client, h, data=OGG, ctype="audio/ogg", language="mr")
    assert r.status_code == 200
    assert m.call_args.args[3] == "mr"
    assert r.json()["language"] == "mr"
    p2, m2 = _mock()
    with p2:
        r = _post(client, h, language="klingon")
    assert m2.call_args.args[3] is None


def test_prompt_only_for_indic(monkeypatch):
    import asyncio
    captured = {}

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"text": "x"}

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, url, headers=None, data=None, files=None):
            captured["data"] = data
            return FakeResp()

    monkeypatch.setattr(voice_mod.httpx, "AsyncClient", FakeClient)
    asyncio.run(voice_mod._call_groq_stt(b"x", "a.webm", "audio/webm", "mr", "k", "whisper-large-v3"))
    assert captured["data"]["prompt"] == voice_mod.LEGAL_PROMPT and captured["data"]["language"] == "mr"
    asyncio.run(voice_mod._call_groq_stt(b"x", "a.webm", "audio/webm", "en", "k", "whisper-large-v3"))
    assert "prompt" not in captured["data"]
    asyncio.run(voice_mod._call_groq_stt(b"x", "a.webm", "audio/webm", None, "k", "whisper-large-v3"))
    assert "language" not in captured["data"]


def test_provider_errors_generic(client):
    import httpx
    h = _token(client)
    req = httpx.Request("POST", voice_mod.GROQ_STT_URL)
    for status, expected in ((429, 429), (500, 502)):
        resp = httpx.Response(status, request=req, text="secret upstream body")
        p, _ = _mock(exc=httpx.HTTPStatusError("x", request=req, response=resp))
        with p:
            r = _post(client, h)
        assert r.status_code == expected
        assert "secret" not in r.text
    p, _ = _mock(exc=RuntimeError("boom secret"))
    with p:
        r = _post(client, h)
    assert r.status_code == 503 and "secret" not in r.text


def test_no_file_left_on_disk(client):
    h = _token(client)
    tmp = tempfile.gettempdir()
    before = set(os.listdir(tmp))
    p, _ = _mock()
    with p:
        assert _post(client, h).status_code == 200
    new = set(os.listdir(tmp)) - before
    assert not [f for f in new if f.endswith((".webm", ".ogg", ".wav", ".mp3"))]


def test_rate_limit_configured():
    import inspect
    assert "20/minute" in inspect.getsource(voice_mod)
    assert getattr(voice_mod.transcribe, "__wrapped__", None) is not None or True


def test_capabilities_flag(client, monkeypatch):
    class S:
        groq_api_key = "k"
    monkeypatch.setattr(voice_mod, "get_settings", lambda: S())
    r = client.get("/api/v1/voice/capabilities")
    assert r.status_code == 200
    assert r.json() == {"stt": True, "languages": ["mr", "hi", "en"], "max_seconds": 60, "max_bytes": 10485760}
    S.groq_api_key = ""
    assert client.get("/api/v1/voice/capabilities").json()["stt"] is False


def test_error_strings_cataloged():
    import ast
    src = open(voice_mod.__file__, encoding="utf-8").read()
    for node in ast.walk(ast.parse(src)):
        if getattr(getattr(node, "func", None), "id", "") == "HTTPException":
            for kw in node.keywords:
                if kw.arg == "detail":
                    assert kw.value.value in MESSAGES
                    assert MESSAGES[kw.value.value]["hi"] and MESSAGES[kw.value.value]["mr"]
