"""Server-side document reads must go through services.storage.read_document_bytes
(private Cloudinary assets cannot be fetched with a raw httpx.get(file_url)). Storage is mocked."""

import asyncio
import re
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from database import get_db_ctx
from limiter import limiter

PW = "Str0ng-pass!"
BACKEND = Path(__file__).resolve().parent.parent
PRIVATE_URL = "https://res.cloudinary.com/democloud/raw/authenticated/v1/documents/abc.pdf"


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
    email = f"st_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": "S", "email": email, "password": PW})
    assert r.status_code == 201
    client.cookies.clear()
    return r.json()["access_token"], r.json()["user"]["id"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_doc(uid, file_url):
    doc_id = f"doc-st-{uuid.uuid4().hex[:8]}"

    async def go():
        async with get_db_ctx() as db:
            await db.execute(
                "INSERT INTO documents (id, user_id, filename, file_url, file_size, document_type, file_hash, status, uploaded_at) "
                "VALUES ($1,$2,'f.pdf',$3,1,'',$4,'ready',$5)",
                doc_id, uid, file_url, uuid.uuid4().hex, datetime.utcnow().isoformat(),
            )
    asyncio.run(go())
    return doc_id


def test_no_raw_httpx_fetch_of_file_url_in_backend():
    """Grep-style guard: no module fetches a stored file_url with a raw HTTP client."""
    offenders = []
    for path in BACKEND.rglob("*.py"):
        parts = set(path.relative_to(BACKEND).parts)
        if parts & {"venv", "tests", "alembic", "__pycache__", "scripts"} or path.name == "storage.py":
            continue
        src = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(client|httpx|requests|session)\.get\(\s*(doc\[|doc\.get\(|row\[)?\s*[\"']?file_url", src):
            offenders.append(str(path))
    assert not offenders, offenders
    for rel in ("routers/analyze.py", "routers/chat.py"):
        src = (BACKEND / rel).read_text(encoding="utf-8")
        assert "httpx" not in src, rel
        assert "read_document_bytes" in src, rel


def test_chat_reads_private_file_via_storage(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, PRIVATE_URL)
    reader = AsyncMock(return_value=b"%PDF-fake")
    with patch("routers.chat.storage.read_document_bytes", reader), \
         patch("routers.chat.get_doc_text", AsyncMock(return_value=None)), \
         patch("routers.chat.set_doc_text", AsyncMock()), \
         patch("routers.chat.extract_text_from_pdf_str", return_value="doc text"), \
         patch("routers.chat.answer_question_about_document", AsyncMock(return_value="ok")):
        r = client.post("/api/v1/chat", json={"document_id": doc_id, "question": "q"}, headers=_h(token))
    assert r.status_code == 200, r.text
    reader.assert_awaited_once_with(PRIVATE_URL)


def test_chat_storage_failure_is_generic_500(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, PRIVATE_URL)
    with patch("routers.chat.storage.read_document_bytes", AsyncMock(side_effect=RuntimeError("secret-host-detail"))), \
         patch("routers.chat.get_doc_text", AsyncMock(return_value=None)):
        r = client.post("/api/v1/chat", json={"document_id": doc_id, "question": "q"}, headers=_h(token))
    assert r.status_code == 500
    assert "secret-host-detail" not in r.text


def test_chat_multi_falls_back_to_storage(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, PRIVATE_URL)
    reader = AsyncMock(return_value=b"%PDF-fake")
    with patch("routers.chat.storage.read_document_bytes", reader), \
         patch("routers.chat.get_doc_text", AsyncMock(return_value=None)), \
         patch("routers.chat.set_doc_text", AsyncMock()), \
         patch("routers.chat.extract_text_from_pdf_str", return_value="multi text"), \
         patch("routers.chat.answer_question_about_document", AsyncMock(return_value="ok")) as ans:
        r = client.post("/api/v1/chat/multi", json={"document_ids": [doc_id], "question": "q"}, headers=_h(token))
    assert r.status_code == 200, r.text
    reader.assert_awaited_once_with(PRIVATE_URL)
    assert "multi text" in ans.call_args.args[0]


def test_analyze_reads_via_storage_and_enqueues(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, PRIVATE_URL)
    reader = AsyncMock(return_value=b"%PDF-fake")
    enq = AsyncMock(return_value="job-1")
    with patch("routers.analyze.storage.read_document_bytes", reader), \
         patch("worker.enqueue_analysis", enq):
        r = client.post("/api/v1/analyze", json={"document_id": doc_id, "force_reanalyze": True}, headers=_h(token))
    assert r.status_code < 500, r.text
    reader.assert_awaited_once_with(PRIVATE_URL)
    assert enq.await_args.kwargs["file_bytes"] == b"%PDF-fake"


def test_analyze_missing_local_file_is_404(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, "local:///definitely/missing.pdf")
    r = client.post("/api/v1/analyze", json={"document_id": doc_id, "force_reanalyze": True}, headers=_h(token))
    assert r.status_code == 404, r.text


def test_analyze_storage_error_is_generic_500(client):
    token, uid = _register(client)
    doc_id = _seed_doc(uid, PRIVATE_URL)
    with patch("routers.analyze.storage.read_document_bytes", AsyncMock(side_effect=RuntimeError("boom-internal"))):
        r = client.post("/api/v1/analyze", json={"document_id": doc_id, "force_reanalyze": True}, headers=_h(token))
    assert r.status_code == 500
    assert "boom-internal" not in r.text
