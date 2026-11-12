"""Deployment-blocker security fixes: password rules, admin-only ingestion, streamed upload limit, Cloudinary cleanup."""

import uuid
from unittest.mock import patch

from routers.auth import settings as auth_settings
from routers.upload import _cloudinary_public_id


def _register(client, password="Str0ng-pass!", email=None):
    email = email or f"sec_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": "Sec Test", "email": email, "password": password})
    return r, email


def test_short_password_rejected(client):
    r, _ = _register(client, password="short")
    assert r.status_code == 422
    assert "8 characters" in r.text


def test_register_and_login_still_work(client):
    r, email = _register(client)
    assert r.status_code == 201
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "Str0ng-pass!"})
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_ingest_notice_requires_login(client):
    r = client.post("/api/v1/yojana/ingest-notice", json={"text": "x" * 80})
    assert r.status_code == 401


def test_ingest_notice_requires_admin_email(client):
    r, email = _register(client)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Logged in but not an admin (ADMIN_EMAILS empty) -> forbidden
    denied = client.post("/api/v1/yojana/ingest-notice", json={"text": "x" * 80}, headers=headers)
    assert denied.status_code == 403

    # Listed as admin -> passes the auth gate (then fails on our deliberately too-short text, i.e. past auth)
    with patch.object(auth_settings, "admin_emails", email):
        allowed = client.post("/api/v1/yojana/ingest-notice", json={"text": "too short"}, headers=headers)
    assert allowed.status_code == 400


def test_upload_over_limit_is_rejected_before_validation(client):
    r, _ = _register(client)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    big = b"%PDF-1.4\n" + b"0" * (26 * 1024 * 1024)
    resp = client.post("/api/v1/upload", files={"file": ("big.pdf", big, "application/pdf")}, headers=headers)
    assert resp.status_code == 400
    assert "too large" in resp.text.lower()


def test_cloudinary_public_id_parsing():
    url = "https://res.cloudinary.com/demo/raw/upload/v1731300000/smartlegal/user-1/abc-123"
    assert _cloudinary_public_id(url) == "smartlegal/user-1/abc-123"
    assert _cloudinary_public_id("https://res.cloudinary.com/demo/raw/upload/smartlegal/u/x?foo=1") == "smartlegal/u/x"
    assert _cloudinary_public_id("local:///tmp/file.pdf") is None
