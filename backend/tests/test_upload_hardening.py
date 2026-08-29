"""
test_upload_hardening.py — Upload & Rate-Limit Hardening Security Tests (SL-046).

Verifies strict validation of file size limits, magic bytes integrity,
and file type checking.
"""

import pytest
import io


def test_oversized_file_rejected(client, auth_headers_user_a):
    """Oversized file (>10MB) must be rejected with 400 Bad Request."""
    large_content = b"0" * (11 * 1024 * 1024)  # 11 MB
    file_obj = ("huge.pdf", io.BytesIO(large_content), "application/pdf")

    resp = client.post(
        "/api/v1/upload",
        files={"file": file_obj},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 400
    assert "File too large" in resp.json()["detail"]


def test_invalid_magic_bytes_rejected(client, auth_headers_user_a):
    """File claiming to be PDF but containing executable binary bytes must be rejected."""
    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00"  # Windows EXE magic header
    file_obj = ("malicious.pdf", io.BytesIO(fake_pdf), "application/pdf")

    resp = client.post(
        "/api/v1/upload",
        files={"file": file_obj},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_unsupported_file_extension(client, auth_headers_user_a):
    """Unsupported extension (.exe, .zip) must be rejected."""
    exe_file = ("script.exe", io.BytesIO(b"MZ12345"), "application/octet-stream")

    resp = client.post(
        "/api/v1/upload",
        files={"file": exe_file},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 400

