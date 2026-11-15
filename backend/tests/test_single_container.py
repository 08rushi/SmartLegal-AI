"""Single-container deployment: SPA serving, platform URL trust, SMTP fallback (no network)."""
import asyncio
import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _restore_main_module():
    """Reloading `main` here must not leak a different app instance into other test files."""
    original = sys.modules.get("main")
    yield
    if original is not None:
        sys.modules["main"] = original
    else:
        sys.modules.pop("main", None)


def _reload_main(monkeypatch, static_dir):
    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    sys.modules.pop("main", None)
    return importlib.import_module("main")


@pytest.fixture
def static_dir(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('x')")
    (tmp_path / "index.html").write_text("<html><body>SPA</body></html>")
    (tmp_path / "robots.txt").write_text("User-agent: *")
    return tmp_path


def test_spa_served_with_api_untouched(monkeypatch, static_dir):
    main = _reload_main(monkeypatch, static_dir)
    c = TestClient(main.app)
    assert "SPA" in c.get("/").text
    assert "SPA" in c.get("/services/deep/link").text           # client-side route fallback
    assert c.get("/assets/app.js").text.startswith("console.log")
    assert c.get("/robots.txt").text.startswith("User-agent")   # real file at root
    assert c.get("/health").json()["status"] == "ok"            # API wins over the fallback
    r = c.get("/api/v1/nope")
    assert r.status_code == 404 and "SPA" not in r.text         # unknown API path is not the SPA


def test_path_traversal_does_not_escape(monkeypatch, static_dir):
    main = _reload_main(monkeypatch, static_dir)
    c = TestClient(main.app)
    r = c.get("/..%2f..%2fconfig.py")
    assert "SPA" in r.text or r.status_code == 404
    assert "class Settings" not in r.text


def test_root_json_when_no_frontend(monkeypatch, tmp_path):
    main = _reload_main(monkeypatch, tmp_path / "missing")
    r = TestClient(main.app).get("/")
    assert r.json()["message"].startswith("SmartLegal AI API")


def test_platform_url_trusted_as_origin(monkeypatch):
    import config
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://smartlegal-abc.onrender.com/")
    s = config.Settings(allowed_origins="http://localhost:5173")
    config._apply_platform_url(s)
    assert s.allowed_origins == "https://smartlegal-abc.onrender.com"
    assert s.frontend_url == "https://smartlegal-abc.onrender.com"
    monkeypatch.delenv("RENDER_EXTERNAL_URL")
    monkeypatch.setenv("KOYEB_PUBLIC_DOMAIN", "x.koyeb.app")
    s2 = config.Settings(allowed_origins="http://localhost:5173")
    config._apply_platform_url(s2)
    assert s2.allowed_origins == "https://x.koyeb.app"


def test_smtp_used_when_resend_absent(monkeypatch):
    import config
    from services import email_service as es
    sent = {}
    monkeypatch.setattr(es, "_send_smtp_blocking", lambda to, sub, h, t: sent.update(to=to, sub=sub))
    cfg = config.Settings(SMTP_HOST="smtp.example.com", SMTP_USER="u@example.com", SMTP_PASSWORD="pw",
                          RESEND_API_KEY="", EMAIL_FROM="")
    monkeypatch.setattr(es, "get_settings", lambda: cfg)
    assert es.email_configured()
    ok = asyncio.run(es.send_email("a@b.com", "subj", "<p>x</p>", "x"))
    assert ok and sent["to"] == "a@b.com"


def test_smtp_failure_never_raises(monkeypatch):
    import config
    from services import email_service as es

    def boom(*a, **k):
        raise OSError("down")

    monkeypatch.setattr(es, "_send_smtp_blocking", boom)
    cfg = config.Settings(SMTP_HOST="smtp.example.com", SMTP_USER="u", SMTP_PASSWORD="pw")
    monkeypatch.setattr(es, "get_settings", lambda: cfg)
    assert asyncio.run(es.send_email("a@b.com", "s", "h", "t")) is False
