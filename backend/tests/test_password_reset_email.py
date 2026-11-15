"""Password-reset email via Resend (only the outbound HTTP call is mocked)."""
import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from routers import auth as auth_router
from services import email_service
from limiter import limiter
from database import get_db
from main import app

URL = "/api/v1/auth/forgot-password"


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    try:
        limiter.reset()
    except Exception:
        pass
    s = auth_router.settings
    monkeypatch.setattr(s, "environment", "development", raising=False)
    monkeypatch.setattr(s, "resend_api_key", "", raising=False)
    monkeypatch.setattr(s, "email_from", "", raising=False)
    monkeypatch.setattr(s, "frontend_url", "http://localhost:5173", raising=False)
    _set_user({"id": "u1"})
    yield
    app.dependency_overrides.pop(get_db, None)


def _set_user(row):
    db = MagicMock()
    db.fetchrow = AsyncMock(return_value=row)
    db.execute = AsyncMock(return_value=None)

    async def _dep():
        yield db

    app.dependency_overrides[get_db] = _dep


def _configure(monkeypatch):
    s = auth_router.settings
    monkeypatch.setattr(s, "resend_api_key", "re_test_key", raising=False)
    monkeypatch.setattr(s, "email_from", "SmartLegal <no-reply@example.com>", raising=False)


def _mock_post(monkeypatch, status=200, exc=None):
    post = AsyncMock()
    if exc:
        post.side_effect = exc
    else:
        post.return_value = MagicMock(status_code=status)
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    return post


def test_email_sent_with_link(client, monkeypatch):
    _configure(monkeypatch)
    post = _mock_post(monkeypatch)
    r = client.post(URL, json={"email": "a@example.com"})
    assert r.status_code == 200
    assert "reset_token" not in r.json()
    assert post.await_count == 1
    args, kwargs = post.call_args
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    body = kwargs["json"]
    assert body["to"] == ["a@example.com"]
    assert body["from"] == "SmartLegal <no-reply@example.com>"
    assert "http://localhost:5173/reset-password?token=" in body["text"]
    assert "http://localhost:5173/reset-password?token=" in body["html"]


def test_unknown_email_not_sent_same_response(client, monkeypatch):
    _configure(monkeypatch)
    post = _mock_post(monkeypatch)
    known = client.post(URL, json={"email": "a@example.com"}).json()
    _set_user(None)
    post.reset_mock()
    unknown = client.post(URL, json={"email": "nobody@example.com"})
    assert unknown.status_code == 200
    assert unknown.json() == known
    assert post.await_count == 0


def test_no_token_in_production(client, monkeypatch, capsys):
    monkeypatch.setattr(auth_router.settings, "environment", "production", raising=False)
    r = client.post(URL, json={"email": "a@example.com"})
    assert r.status_code == 200
    assert "reset_token" not in r.json() and "expires_at" not in r.json()
    assert "Password reset token" not in capsys.readouterr().out


def test_no_token_in_production_with_email(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(auth_router.settings, "environment", "production", raising=False)
    _mock_post(monkeypatch)
    r = client.post(URL, json={"email": "a@example.com"})
    assert "reset_token" not in r.json()


def test_dev_fallback_unchanged(client, monkeypatch):
    post = _mock_post(monkeypatch)
    r = client.post(URL, json={"email": "a@example.com"})
    assert r.status_code == 200
    assert r.json().get("reset_token")
    assert post.await_count == 0


@pytest.mark.parametrize("kind", ["status", "exception"])
def test_resend_failure_does_not_break(client, monkeypatch, kind):
    _configure(monkeypatch)
    if kind == "status":
        _mock_post(monkeypatch, status=500)
    else:
        _mock_post(monkeypatch, exc=httpx.ConnectError("boom"))
    r = client.post(URL, json={"email": "a@example.com"})
    assert r.status_code == 200
    assert "reset_token" not in r.json()


def test_send_returns_bool(monkeypatch):
    import asyncio
    _configure(monkeypatch)
    _mock_post(monkeypatch, status=200)
    assert asyncio.run(email_service.send_password_reset_email("a@example.com", "tok", 30)) is True
    _mock_post(monkeypatch, status=422)
    assert asyncio.run(email_service.send_password_reset_email("a@example.com", "tok", 30)) is False
