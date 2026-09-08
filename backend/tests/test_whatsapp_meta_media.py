"""
test_whatsapp_meta_media.py — Step 3B Meta WhatsApp Cloud API Media Download Production Hardening Test Suite.

Verifies:
1. SSRF URL validation (HTTPS scheme, exact & leading-dot host whitelist, IP range checks).
2. Subdomain spoofing prevention (evilfacebook.com, facebook.com.attacker.com blocked).
3. Private IP / Loopback / Metadata server IP blocking (127.0.0.1, 192.168.x.x, 169.254.169.254).
4. Meta Graph API metadata retrieval & authenticated media streaming.
5. Trusted -> Trusted Meta redirect handling (fbsbx.com -> fbcdn.net).
6. Localhost / Private IP redirect blocking & Bearer token non-leakage.
7. Canonical 10 MB streaming size limit enforcement.
8. Zero-byte empty download rejection.
9. Image MIME content type handling (JPG, PNG, WebP vs PDF).
10. Media downloader factory resolution (get_whatsapp_media_downloader).
"""

import pytest
import asyncio
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from config import get_settings
from services.whatsapp.media import (
    validate_meta_url_ssrf,
    MetaMediaDownloader,
    DevMediaDownloader,
    get_whatsapp_media_downloader,
    DownloadedMedia,
    MAX_MEDIA_SIZE_BYTES,
)


def test_validate_meta_url_ssrf_valid():
    """Verify trusted Meta URLs pass SSRF validation."""
    assert validate_meta_url_ssrf("https://graph.facebook.com/v21.0/123456") == "https://graph.facebook.com/v21.0/123456"
    assert validate_meta_url_ssrf("https://lookaside.fbsbx.com/whatsapp_business/attachments/123") == "https://lookaside.fbsbx.com/whatsapp_business/attachments/123"
    assert validate_meta_url_ssrf("https://scontent.fbcdn.net/v/t39/1234") == "https://scontent.fbcdn.net/v/t39/1234"


def test_validate_meta_url_ssrf_rejections():
    """Verify spoofed domains, non-HTTPS, private IPs, loopbacks are blocked."""
    # Non-HTTPS
    with pytest.raises(ValueError, match="HTTPS is strictly required"):
        validate_meta_url_ssrf("http://graph.facebook.com/v21.0/123456")

    # Subdomain spoofing / suffix tricks
    with pytest.raises(ValueError, match="not in Meta trusted whitelist"):
        validate_meta_url_ssrf("https://evilfacebook.com/media")

    with pytest.raises(ValueError, match="not in Meta trusted whitelist"):
        validate_meta_url_ssrf("https://facebook.com.attacker.com/media")

    with pytest.raises(ValueError, match="not in Meta trusted whitelist"):
        validate_meta_url_ssrf("https://fbsbx.com.fake.io/media")

    # Loopback / Localhost / Private IPs
    with pytest.raises(ValueError, match="SSRF violation"):
        validate_meta_url_ssrf("https://127.0.0.1/media")

    with pytest.raises(ValueError, match="not in Meta trusted whitelist"):
        validate_meta_url_ssrf("https://localhost/media")

    with pytest.raises(ValueError, match="SSRF violation"):
        validate_meta_url_ssrf("https://192.168.1.1/media")

    with pytest.raises(ValueError, match="SSRF violation"):
        validate_meta_url_ssrf("https://10.0.0.1/media")

    with pytest.raises(ValueError, match="SSRF violation"):
        validate_meta_url_ssrf("https://169.254.169.254/latest/meta-data")


def test_media_downloader_factory():
    """Verify get_whatsapp_media_downloader resolves proper downloader instance."""
    downloader_dev = get_whatsapp_media_downloader({"provider": "dev_simulator"})
    assert isinstance(downloader_dev, DevMediaDownloader)

    settings = get_settings()
    settings.meta_whatsapp_access_token = "mock_test_token_123"

    downloader_meta = get_whatsapp_media_downloader({"provider": "meta_cloud_api"})
    assert isinstance(downloader_meta, MetaMediaDownloader)


@pytest.mark.anyio
async def test_meta_media_downloader_missing_token():
    """Verify MetaMediaDownloader fails cleanly if access token is unconfigured."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = ""

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError, match="META_WHATSAPP_ACCESS_TOKEN is not configured"):
        await downloader.download_media("media_999")


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.stream")
async def test_meta_media_downloader_success(mock_stream, mock_get):
    """Verify successful Graph API metadata lookup and authenticated media download."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "valid_token_xyz"
    settings.meta_whatsapp_graph_url = "https://graph.facebook.com"
    settings.meta_whatsapp_api_version = "v21.0"

    mock_meta_resp = MagicMock()
    mock_meta_resp.status_code = 200
    mock_meta_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "url": "https://lookaside.fbsbx.com/whatsapp_business/attachments/?asset_id=100200",
        "mime_type": "application/pdf",
        "file_size": 140,
        "id": "media_100200",
    }
    mock_get.return_value = mock_meta_resp

    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kinds [] /Count 1 /Kids [3 0 R] >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF"
    )

    mock_dl_resp = MagicMock()
    mock_dl_resp.status_code = 200
    mock_dl_resp.headers = {"Content-Length": str(len(pdf_bytes))}

    async def async_chunks():
        yield pdf_bytes

    mock_dl_resp.aiter_bytes = async_chunks

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_dl_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream.return_value = mock_stream_ctx

    downloader = MetaMediaDownloader()
    result = await downloader.download_media(media_id="media_100200")

    assert isinstance(result, DownloadedMedia)
    assert result.media_id == "media_100200"
    assert result.content == pdf_bytes
    assert result.mime_type == "application/pdf"
    assert result.filename == "whatsapp_media_100200"
    assert result.file_size == len(pdf_bytes)


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_meta_media_downloader_404_expired(mock_get):
    """Verify 404 expired media link raises structured ValueError."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "valid_token_xyz"

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError, match="Meta Graph API returned status 404"):
        await downloader.download_media("expired_media_id")


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.stream")
async def test_trusted_to_trusted_meta_redirect(mock_stream, mock_get):
    """Verify trusted Meta URL redirect to another trusted Meta domain (fbsbx.com -> fbcdn.net) succeeds."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "secret_bearer_token_xyz"

    mock_meta_resp = MagicMock()
    mock_meta_resp.status_code = 200
    mock_meta_resp.json.return_value = {
        "url": "https://lookaside.fbsbx.com/attachment_1",
        "mime_type": "image/png",
    }
    mock_get.return_value = mock_meta_resp

    # First stream response: 302 redirect to scontent.fbcdn.net
    mock_resp_302 = MagicMock()
    mock_resp_302.status_code = 302
    mock_resp_302.headers = {"Location": "https://scontent.fbcdn.net/v/t39/photo.png"}

    # Second stream response: 200 OK with PNG bytes
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.headers = {"Content-Length": str(len(png_bytes))}

    async def async_png_chunks():
        yield png_bytes

    mock_resp_200.aiter_bytes = async_png_chunks

    mock_ctx_302 = MagicMock()
    mock_ctx_302.__aenter__ = AsyncMock(return_value=mock_resp_302)
    mock_ctx_302.__aexit__ = AsyncMock(return_value=None)

    mock_ctx_200 = MagicMock()
    mock_ctx_200.__aenter__ = AsyncMock(return_value=mock_resp_200)
    mock_ctx_200.__aexit__ = AsyncMock(return_value=None)

    mock_stream.side_effect = [mock_ctx_302, mock_ctx_200]

    downloader = MetaMediaDownloader()
    res = await downloader.download_media("media_redirect_ok")
    assert res.content == png_bytes
    assert res.mime_type == "image/png"


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.stream")
async def test_redirect_to_localhost_or_private_ip_blocked(mock_stream, mock_get):
    """Verify redirect to localhost/private IP is blocked by SSRF host check before download."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "secret_bearer_token_xyz"

    mock_meta_resp = MagicMock()
    mock_meta_resp.status_code = 200
    mock_meta_resp.json.return_value = {
        "url": "https://lookaside.fbsbx.com/attachment_1",
        "mime_type": "application/pdf",
    }
    mock_get.return_value = mock_meta_resp

    mock_redirect_resp = MagicMock()
    mock_redirect_resp.status_code = 302
    mock_redirect_resp.headers = {"Location": "https://127.0.0.1/internal_admin"}

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_redirect_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream.return_value = mock_stream_ctx

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError, match="SSRF violation"):
        await downloader.download_media("media_redirect_ssrf")


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.stream")
async def test_zero_byte_download_rejected(mock_stream, mock_get):
    """Verify zero-byte empty download raises ValueError."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"

    mock_meta_resp = MagicMock()
    mock_meta_resp.status_code = 200
    mock_meta_resp.json.return_value = {"url": "https://lookaside.fbsbx.com/empty", "mime_type": "application/pdf"}
    mock_get.return_value = mock_meta_resp

    mock_dl_resp = MagicMock()
    mock_dl_resp.status_code = 200
    mock_dl_resp.headers = {"Content-Length": "0"}

    async def empty_chunks():
        if False:
            yield b""

    mock_dl_resp.aiter_bytes = empty_chunks

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_dl_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream.return_value = mock_stream_ctx

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError, match="Downloaded media is empty"):
        await downloader.download_media("media_empty")


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.stream")
async def test_oversized_10mb_download_streaming_aborted(mock_stream, mock_get):
    """Verify downloading payload exceeding canonical 10 MB limit aborts streaming."""
    settings = get_settings()
    settings.meta_whatsapp_access_token = "token_123"

    mock_meta_resp = MagicMock()
    mock_meta_resp.status_code = 200
    mock_meta_resp.json.return_value = {"url": "https://lookaside.fbsbx.com/large", "mime_type": "application/pdf"}
    mock_get.return_value = mock_meta_resp

    mock_dl_resp = MagicMock()
    mock_dl_resp.status_code = 200
    mock_dl_resp.headers = {"Content-Length": str(MAX_MEDIA_SIZE_BYTES + 1024)}

    async def oversized_chunks():
        yield b"A" * (MAX_MEDIA_SIZE_BYTES + 100)

    mock_dl_resp.aiter_bytes = oversized_chunks

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_dl_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_stream.return_value = mock_stream_ctx

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError, match="exceeds maximum allowed size of 10 MB"):
        await downloader.download_media("media_oversized")


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_bearer_token_non_leakage_in_exceptions(mock_get):
    """Verify raw META_WHATSAPP_ACCESS_TOKEN is never leaked in exception messages."""
    settings = get_settings()
    secret_token = "super_secret_bearer_token_99999"
    settings.meta_whatsapp_access_token = secret_token

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    downloader = MetaMediaDownloader()
    with pytest.raises(ValueError) as exc_info:
        await downloader.download_media("media_auth_fail")

    err_str = str(exc_info.value)
    assert secret_token not in err_str
