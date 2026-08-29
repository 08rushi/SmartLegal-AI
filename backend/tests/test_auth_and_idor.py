"""
test_auth_and_idor.py — Authentication & Object-Level Authorization Security Tests (SL-044 / SL-045).
"""

import pytest
from unittest.mock import AsyncMock


def test_unauthenticated_protected_route_denied(client):
    """Verify protected history route requires authentication."""
    resp = client.get("/api/v1/upload/history")
    assert resp.status_code == 401


def test_idor_document_access_denied(client, mock_db_pool, auth_headers_user_a, auth_headers_user_b):
    """
    IDOR Security Test (SL-045):
    User A owns Document 'doc_a_123'.
    User B attempts to get details, download, analyze, chat, and delete User A's document.
    All attempts MUST be rejected with 403 Forbidden.
    """
    # Mock document belonging to User A ('user_a_id_12345')
    doc_user_a = {
        "id": "doc_a_123",
        "user_id": "user_a_id_12345",
        "filename": "user_a_contract.pdf",
        "file_path": "uploads/user_a_contract.pdf",
        "file_size": 1024,
        "file_hash": "sha256hash123",
        "document_type": "Rental Agreement",
        "status": "ready",
        "uploaded_at": "2026-08-29T00:00:00Z",
    }
    mock_db_pool.fetchrow = AsyncMock(return_value=doc_user_a)

    doc_id = "doc_a_123"

    # 1. User B tries to get metadata for User A's document -> 401 or 403
    get_resp = client.get(f"/api/v1/upload/{doc_id}", headers=auth_headers_user_b)
    assert get_resp.status_code in (401, 403)

    # 2. User B tries to download User A's private document -> 401 or 403
    download_resp = client.get(f"/api/v1/upload/{doc_id}/download", headers=auth_headers_user_b)
    assert download_resp.status_code in (401, 403)

    # 3. User B tries to analyze User A's document -> 401 or 403
    analyze_resp = client.post(
        "/api/v1/analyze",
        json={"document_id": doc_id, "force_reanalyze": False},
        headers=auth_headers_user_b
    )
    assert analyze_resp.status_code in (401, 403)

    # 4. User B tries to send chat question on User A's document -> 401 or 403
    chat_resp = client.post(
        "/api/v1/chat",
        json={"document_id": doc_id, "question": "What is the rent?"},
        headers=auth_headers_user_b
    )
    assert chat_resp.status_code in (401, 403)

    # 5. User B tries to delete User A's document -> 401 or 403
    delete_resp = client.delete(f"/api/v1/upload/{doc_id}", headers=auth_headers_user_b)
    assert delete_resp.status_code in (401, 403)


