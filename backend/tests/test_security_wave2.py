"""Security wave 2: fail-closed env, login-required upload, Google linking, private Cloudinary
files, cookie-only auth + CSRF. SQLite and mocks only; no network."""
import asyncio
import io
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import auth_google
import config as config_mod
from config import Settings
from database import get_db_ctx
from limiter import limiter
from routers import auth as auth_router
from routers import upload as upload_router
from services import storage

PW = "Str0ng-pass!"
MIN_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)
ORIGIN = "http://localhost:5173"
CLOUD = "democloud"


@pytest.fixture(autouse=True)
def _clean(client):
    client.cookies.clear()
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    client.cookies.clear()


def _register(client):
    email = f"w2_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": "W2", "email": email, "password": PW})
    assert r.status_code == 201
    client.cookies.clear()
    return email, r.json()["access_token"], r.json()["user"]["id"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _upload(client, headers=None):
    body = MIN_PDF + uuid.uuid4().hex.encode()
    return client.post("/api/v1/upload", files={"file": ("a.pdf", io.BytesIO(body), "application/pdf")},
                       headers=headers or {})


def _mk(**kw):
    return Settings(_env_file=None, **kw)


# ── #1 fail-closed environment ───────────────────────────────────────────────

def test_environment_defaults_to_production(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    s = _mk()
    assert s.environment == "production" and s.is_production and not s.is_development
    for v in ("development", "dev", "test", "testing"):
        assert _mk(ENVIRONMENT=v).is_development
    assert _mk(ENVIRONMENT="staging").is_production
    assert _mk(ENVIRONMENT="").is_production


def test_unset_environment_fails_production_validation(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    errors, _ = config_mod.validate_production_config(_mk(SECRET_KEY="short"))
    assert errors  # sqlite url / secret / origins / cloudinary all rejected


def test_reset_token_needs_dev_and_explicit_flag(client):
    email, _, _ = _register(client)
    s = auth_router.settings

    def forgot():
        limiter.reset()
        with patch.object(auth_router, "email_configured", return_value=False):
            return client.post("/api/v1/auth/forgot-password", json={"email": email}).json()

    with patch.object(s, "environment", "development"), patch.object(s, "expose_reset_token_in_response", False):
        assert "reset_token" not in forgot()
    with patch.object(s, "environment", "development"), patch.object(s, "expose_reset_token_in_response", True):
        assert "reset_token" in forgot()
    with patch.object(s, "environment", "production"), patch.object(s, "expose_reset_token_in_response", True):
        assert "reset_token" not in forgot()


def test_default_expose_flag_is_false(monkeypatch):
    monkeypatch.delenv("EXPOSE_RESET_TOKEN_IN_RESPONSE", raising=False)
    monkeypatch.delenv("AUTH_RETURN_BODY_TOKEN", raising=False)
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    assert _mk().expose_reset_token_in_response is False
    assert _mk().auth_return_body_token is False
    assert _mk().access_token_expire_minutes == 1440


# ── #3 upload requires login ─────────────────────────────────────────────────

def test_upload_and_history_require_login(client):
    assert _upload(client).status_code == 401
    assert client.get("/api/v1/upload/history").status_code == 401


def test_upload_response_has_no_file_url(client):
    _, token, _ = _register(client)
    r = _upload(client, _h(token))
    assert r.status_code == 201
    doc = r.json()["document"]
    assert "file_url" not in doc
    did = doc["id"]
    assert "file_url" not in client.get(f"/api/v1/upload/{did}", headers=_h(token)).json()
    hist = client.get("/api/v1/upload/history", headers=_h(token)).json()["documents"]
    assert hist and all("file_url" not in d for d in hist)
    # duplicate upload path (reuse) also omits it
    again = client.post("/api/v1/upload", files={"file": ("a.pdf", io.BytesIO(MIN_PDF), "application/pdf")},
                        headers=_h(token))
    assert "file_url" not in again.json()["document"]


def test_get_optional_user_removed():
    assert not hasattr(auth_router, "get_optional_user")


# ── #6 Google linking ────────────────────────────────────────────────────────

def _google(client, email):
    payload = {"aud": "cid", "iss": "accounts.google.com", "email_verified": "true", "email": email, "name": "G"}
    resp = MagicMock(status_code=200)
    resp.json.return_value = payload
    fake_client = MagicMock()
    fake_client.get = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=fake_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    with patch.object(auth_google.settings, "google_client_id", "cid"), \
         patch.object(auth_google.httpx, "AsyncClient", return_value=cm):
        return client.post("/api/v1/auth/google", json={"credential": "x"})


def test_google_link_invalidates_password_and_sessions(client, capsys):
    email, old_token, uid = _register(client)
    assert client.post("/api/v1/auth/login", data={"username": email, "password": PW}).status_code == 200
    client.cookies.clear()

    r = _google(client, email)
    assert r.status_code == 200
    client.cookies.clear()
    # old password no longer works, old session revoked
    assert client.post("/api/v1/auth/login", data={"username": email, "password": PW}).status_code == 401
    assert client.get("/api/v1/auth/me", headers=_h(old_token)).status_code == 401
    # new Google session works
    new_token = r.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=_h(new_token)).status_code == 200
    # no PII in log
    assert email not in capsys.readouterr().out
    # a second Google sign-in must NOT keep revoking sessions
    r2 = _google(client, email)
    client.cookies.clear()
    assert client.get("/api/v1/auth/me", headers=_h(new_token)).status_code == 200
    assert r2.status_code == 200
    # password reset still possible (hash is non-empty marker)
    async def pw():
        async with get_db_ctx() as db:
            return (await db.fetchrow("SELECT password FROM users WHERE id = $1", uid))["password"]
    assert asyncio.run(pw()).startswith(auth_google.UNUSABLE_PASSWORD_PREFIX)


def test_google_new_user_unaffected(client):
    r = _google(client, f"newg_{uuid.uuid4().hex[:6]}@example.com")
    assert r.status_code == 200 and r.json()["user"]["email"].startswith("newg_")


# ── #4 private Cloudinary files ──────────────────────────────────────────────

@pytest.fixture
def cloud(monkeypatch):
    for obj in (storage.settings, upload_router.settings):
        monkeypatch.setattr(obj, "cloudinary_cloud_name", CLOUD)
        monkeypatch.setattr(obj, "cloudinary_api_key", "key")
        monkeypatch.setattr(obj, "cloudinary_api_secret", "secret")
    return CLOUD


def test_store_file_uploads_authenticated(cloud):
    fake = MagicMock(return_value={"secure_url": f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/v1/smartlegal/u/x"})
    with patch("cloudinary.uploader.upload", fake):
        url = upload_router._store_file(b"%PDF-1.4", "a.pdf", "u")
    assert fake.call_args.kwargs["type"] == "authenticated"
    assert fake.call_args.kwargs["resource_type"] == "raw"
    assert "/authenticated/" in url


def test_url_parsing_and_allow_check(cloud):
    pub = f"https://res.cloudinary.com/{CLOUD}/raw/upload/v12/smartlegal/u/x"
    priv = f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/s--abc--/v12/smartlegal/u/x"
    assert storage.parse_cloudinary_url(pub)["type"] == "upload"
    assert storage.parse_cloudinary_url(priv)["public_id"] == "smartlegal/u/x"
    assert upload_router._cloudinary_public_id(priv) == "smartlegal/u/x"
    assert storage.is_allowed_cloud_url(pub) and storage.is_allowed_cloud_url(priv)
    for bad in (
        "http://res.cloudinary.com/democloud/raw/upload/v1/a",
        "https://evil.com/democloud/raw/upload/v1/a",
        "https://res.cloudinary.com.evil.com/democloud/raw/upload/v1/a",
        "https://res.cloudinary.com/othercloud/raw/upload/v1/a",
        "https://169.254.169.254/latest/meta-data",
        "local:///etc/passwd", "", None,
    ):
        assert not storage.is_allowed_cloud_url(bad)


def test_signed_url_is_short_lived_for_private_assets(cloud):
    priv = f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/v12/smartlegal/u/x"
    with patch("time.time", return_value=1_000_000):
        signed = storage.signed_download_url(priv, 300)
    assert signed.startswith("https://api.cloudinary.com/")
    assert "signature=" in signed and "expires_at=1000300" in signed and "type=authenticated" in signed
    with pytest.raises(storage.StorageError):
        storage.signed_download_url("https://evil.com/democloud/raw/authenticated/v1/a")


def _seed_doc(uid, file_url, doc_id=None):
    doc_id = doc_id or str(uuid.uuid4())

    async def go():
        async with get_db_ctx() as db:
            await db.execute(
                "INSERT INTO documents (id, user_id, filename, file_url, file_size, document_type, file_hash, status, uploaded_at) "
                "VALUES ($1,$2,'f.pdf',$3,1,'',$4,'ready',$5)",
                doc_id, uid, file_url, uuid.uuid4().hex, datetime.utcnow().isoformat())
    asyncio.run(go())
    return doc_id


def test_download_redirects_to_signed_url_after_ownership_check(client, cloud):
    _, ta, ua = _register(client)
    _, tb, _ = _register(client)
    did = _seed_doc(ua, f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/v1/smartlegal/{ua}/x")
    assert client.get(f"/api/v1/upload/{did}/download", headers=_h(tb), follow_redirects=False).status_code == 403
    assert client.get(f"/api/v1/upload/{did}/download", follow_redirects=False).status_code == 401
    r = client.get(f"/api/v1/upload/{did}/download", headers=_h(ta), follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"].startswith("https://api.cloudinary.com/") and "signature=" in r.headers["location"]


def test_download_rejects_foreign_host(client, cloud):
    _, ta, ua = _register(client)
    did = _seed_doc(ua, "https://evil.example.com/democloud/raw/upload/v1/x")
    assert client.get(f"/api/v1/upload/{did}/download", headers=_h(ta), follow_redirects=False).status_code == 404


def test_read_document_bytes_uses_signed_url_and_blocks_foreign(cloud):
    priv = f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/v1/smartlegal/u/x"
    seen = {}

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url):
            seen["url"] = url
            r = MagicMock(content=b"%PDF-data")
            r.raise_for_status = MagicMock()
            return r

    import httpx
    with patch.object(httpx, "AsyncClient", FakeClient):
        data = asyncio.run(storage.read_document_bytes(priv))
        assert data == b"%PDF-data" and seen["url"].startswith("https://api.cloudinary.com/") and "signature=" in seen["url"]
        seen.clear()
        with pytest.raises(storage.StorageError):
            asyncio.run(storage.read_document_bytes("https://evil.com/democloud/raw/upload/v1/x"))
        assert not seen  # never requested


def test_migration_script_dry_run_and_apply(cloud):
    import importlib.util, pathlib
    path = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "migrate_cloudinary_to_private.py"
    spec = importlib.util.spec_from_file_location("migrate_cp", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    rows = [
        {"id": "1", "file_url": f"https://res.cloudinary.com/{CLOUD}/raw/upload/v1/smartlegal/u/a"},
        {"id": "2", "file_url": f"https://res.cloudinary.com/{CLOUD}/raw/authenticated/v1/smartlegal/u/b"},
        {"id": "3", "file_url": "local:///tmp/x"},
        {"id": "4", "file_url": "https://evil.com/democloud/raw/upload/v1/a"},
    ]
    conn = MagicMock()
    conn.fetch = AsyncMock(return_value=rows)
    conn.execute = AsyncMock()
    renamed = []

    def fake_rename(url):
        renamed.append(url)
        return url.replace("/upload/", "/authenticated/")

    dry = asyncio.run(mod.migrate(conn, False, rename=fake_rename))
    assert dry["public"] == 1 and dry["private"] == 1 and dry["migrated"] == 0
    assert not renamed and not conn.execute.called
    done = asyncio.run(mod.migrate(conn, True, rename=fake_rename))
    assert done["migrated"] == 1 and len(renamed) == 1 and conn.execute.call_count == 1


# ── #5 cookie-only auth ──────────────────────────────────────────────────────

def test_body_token_off_by_default_cookie_still_set(client):
    email = f"w2_{uuid.uuid4().hex[:8]}@example.com"
    with patch.object(auth_router.settings, "auth_return_body_token", False):
        r = client.post("/api/v1/auth/register", json={"name": "W2", "email": email, "password": PW})
        assert r.status_code == 201
        assert not r.json().get("access_token")
        assert "sl_token" in r.headers["set-cookie"] and "HttpOnly" in r.headers["set-cookie"]
        assert "samesite=lax" in r.headers["set-cookie"].lower()
        client.cookies.clear()
        r = client.post("/api/v1/auth/login", data={"username": email, "password": PW})
        assert r.status_code == 200 and not r.json().get("access_token")
        client.cookies.clear()
    with patch.object(auth_router.settings, "auth_return_body_token", True):
        r = client.post("/api/v1/auth/login", data={"username": email, "password": PW})
        assert r.json()["access_token"]


def test_cookie_secure_flag_in_production():
    resp = MagicMock()
    with patch.object(auth_router.settings, "environment", "production"):
        auth_router._set_auth_cookie(resp, "t")
    assert resp.set_cookie.call_args.kwargs["secure"] is True
    assert resp.set_cookie.call_args.kwargs["samesite"] == "lax"
    with patch.object(auth_router.settings, "environment", "development"):
        auth_router._set_auth_cookie(resp, "t")
    assert resp.set_cookie.call_args.kwargs["secure"] is False


def test_cookie_authenticates_and_no_credential_is_401(client):
    _, token, _ = _register(client)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", cookies={"sl_token": token}).status_code == 200
    client.cookies.clear()
    assert client.get("/api/v1/auth/me", headers=_h(token)).status_code == 200
    # Bearer wins over a bad cookie
    assert client.get("/api/v1/auth/me", headers=_h(token), cookies={"sl_token": "junk"}).status_code == 200


def test_cookie_unsafe_methods_need_allowed_origin(client):
    _, token, _ = _register(client)
    client.cookies.set("sl_token", token)
    # no Origin/Referer -> blocked; evil origin -> blocked; allowed origin / referer -> ok
    assert _upload(client).status_code == 403
    assert _upload(client, {"Origin": "https://evil.example.com"}).status_code == 403
    assert _upload(client, {"Origin": ORIGIN}).status_code == 201
    assert _upload(client, {"Referer": ORIGIN + "/upload"}).status_code == 201
    # safe method needs no Origin
    assert client.get("/api/v1/upload/history").status_code == 200
    client.cookies.clear()
    # Bearer without Origin (non-browser client) is fine
    assert _upload(client, _h(token)).status_code == 201


def test_origin_check_in_production_ignores_localhost_regex():
    with patch.object(auth_router.settings, "environment", "production"), \
         patch.object(auth_router.settings, "allowed_origins", "https://app.example.com"):
        assert auth_router._origin_allowed("https://app.example.com")
        assert not auth_router._origin_allowed("http://localhost:5173")


def test_logout_revokes_and_clears_cookie(client):
    _, token, _ = _register(client)
    r = client.post("/api/v1/auth/logout", headers={**_h(token)})
    assert r.status_code == 200
    assert "sl_token" in r.headers["set-cookie"] and ("max-age=0" in r.headers["set-cookie"].lower()
                                                      or "expires=" in r.headers["set-cookie"].lower())
    assert client.get("/api/v1/auth/me", headers=_h(token)).status_code == 401  # token_version bumped
    # logout without credentials still succeeds
    client.cookies.clear()
    assert client.post("/api/v1/auth/logout", headers={"Origin": ORIGIN}).status_code == 200
    # cookie-only logout from a bad origin is refused
    assert client.post("/api/v1/auth/logout", cookies={"sl_token": token}, headers={"Origin": "https://evil.example.com"}).status_code == 403
