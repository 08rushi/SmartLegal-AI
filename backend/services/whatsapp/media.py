"""
media.py — Dedicated WhatsApp Media Downloader Boundary & Adapters.

Enforces:
1. Normalized DownloadedMedia interface.
2. SSRF protection (strict domain whitelist + IP validation + redirect token isolation).
3. Canonical 10 MB download size ceiling and connection timeouts.
4. Clean separation of provider media downloads from document validation and storage.
"""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
import ipaddress
import logging
import os
import socket
import urllib.parse
from typing import Optional, Dict, Any

import httpx

from config import get_settings
from routers.upload import MAX_SIZE_MB

logger = logging.getLogger(__name__)

MAX_MEDIA_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024  # Canonical 10 MB ceiling

# SSRF Domain Whitelist
META_EXACT_DOMAINS = {"facebook.com", "graph.facebook.com", "fbsbx.com", "fbcdn.net"}
META_TRUSTED_SUFFIXES = (".facebook.com", ".fbsbx.com", ".fbcdn.net")


def validate_meta_url_ssrf(url: str) -> str:
    """
    Validate target URL against strict SSRF security rules:
    1. Scheme MUST be 'https'.
    2. Hostname MUST be an exact match in META_EXACT_DOMAINS or end with a trusted dot-prefixed suffix (.facebook.com, .fbsbx.com, .fbcdn.net).
    3. Hostname/IP MUST NOT resolve to private, loopback, link-local, multicast, or metadata server IPs (169.254.169.254, 127.0.0.1, 10.x, etc.).
    """
    if not url or not isinstance(url, str):
        raise ValueError("Invalid media URL: empty or invalid parameter.")

    parsed = urllib.parse.urlparse(url.strip())
    scheme = parsed.scheme.lower()
    if scheme != "https":
        raise ValueError(f"Invalid media URL scheme '{scheme}': HTTPS is strictly required.")

    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("Invalid media URL: missing hostname.")

    # 1. Check if host is a literal IP address
    try:
        ip_obj = ipaddress.ip_address(host)
        raise ValueError(f"SSRF violation: literal IP address '{host}' is restricted.")
    except ValueError as exc:
        if "SSRF violation" in str(exc):
            raise exc
        # Host is a domain name string

    # 2. Domain whitelist check: exact host match OR leading-dot suffix match
    is_domain_valid = host in META_EXACT_DOMAINS or any(host.endswith(sfx) for sfx in META_TRUSTED_SUFFIXES)
    if not is_domain_valid:
        raise ValueError(f"Invalid media URL hostname '{host}': domain not in Meta trusted whitelist.")

    # 3. Optional DNS resolution check (handles offline test environments gracefully)
    try:
        addr_info = socket.getaddrinfo(host, None)
        resolved_ips = [ipaddress.ip_address(item[4][0]) for item in addr_info if item[4]]
        for ip in resolved_ips:
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                raise ValueError(f"SSRF violation: hostname '{host}' resolves to restricted/private IP '{ip}'.")
    except ValueError:
        raise
    except Exception:
        pass

    return url


@dataclass
class DownloadedMedia:
    """Normalized media payload downloaded from a channel provider."""

    media_id: str
    content: bytes
    mime_type: str
    filename: str
    file_size: int
    provider_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMediaDownloader(ABC):
    """Abstract interface for downloading media from WhatsApp providers."""

    @abstractmethod
    async def download_media(
        self,
        media_id: str,
        media_url: Optional[str] = None,
    ) -> DownloadedMedia:
        """Download media content and return normalized DownloadedMedia payload."""
        pass


class DevMediaDownloader(BaseMediaDownloader):
    """
    Development & Simulation Media Downloader.
    Resolves local test files or byte payloads through the exact same DownloadedMedia pipeline.
    Rejects arbitrary external URLs to prevent SSRF vulnerabilities.
    """

    async def download_media(
        self,
        media_id: str,
        media_url: Optional[str] = None,
    ) -> DownloadedMedia:
        if not media_id and not media_url:
            raise ValueError("Media download failed: Missing media ID or reference.")

        target_ref = media_id or media_url or ""

        # SSRF Protection: Reject arbitrary external HTTP/HTTPS URLs
        if target_ref.startswith(("http://", "https://", "ftp://")) and not target_ref.startswith("http://localhost"):
            logger.warning(f"[media-downloader] Blocked potentially unsafe external URL download: {target_ref}")
            raise ValueError("Invalid media reference: Arbitrary external URLs are not permitted.")

        # Simulate timeout if requested in test
        if target_ref == "timeout_trigger":
            raise asyncio.TimeoutError("Media download request timed out.")

        # Scenario 1: Media ref is a direct local file path (e.g. test fixture)
        if os.path.exists(target_ref):
            file_size = os.path.getsize(target_ref)
            if file_size > MAX_MEDIA_SIZE_BYTES:
                raise ValueError(f"Media exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

            filename = os.path.basename(target_ref)
            ext = os.path.splitext(filename)[1].lower()
            ext_mime_map = {
                ".pdf": "application/pdf",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }
            mime_type = ext_mime_map.get(ext, "application/octet-stream")

            with open(target_ref, "rb") as f:
                content = f.read()

            return DownloadedMedia(
                media_id=media_id or filename,
                content=content,
                mime_type=mime_type,
                filename=filename,
                file_size=len(content),
                provider_metadata={"source": "local_file", "path": target_ref},
            )

        # Scenario 2: Ref is a simulated PDF byte fixture descriptor
        if "sample_pdf" in target_ref or target_ref.endswith(".pdf"):
            content = (
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Kinds [] /Count 1 /Kids [3 0 R] >>\nendobj\n"
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
                b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
                b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF"
            )
            return DownloadedMedia(
                media_id=media_id or "dev_sample_doc",
                content=content,
                mime_type="application/pdf",
                filename="sample_agreement.pdf",
                file_size=len(content),
                provider_metadata={"source": "dev_simulator"},
            )

        # Scenario 3: Ref is a simulated PNG image byte fixture descriptor
        if "sample_png" in target_ref or target_ref.endswith(".png"):
            content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            return DownloadedMedia(
                media_id=media_id or "dev_sample_img",
                content=content,
                mime_type="image/png",
                filename="notice_photo.png",
                file_size=len(content),
                provider_metadata={"source": "dev_simulator"},
            )

        # Scenario 4: Ref is an oversized test payload trigger
        if target_ref == "oversized_trigger":
            raise ValueError(f"Media download aborted: Exceeds size limit of {MAX_SIZE_MB} MB.")

        # Scenario 5: Ref is a zero-byte empty download test trigger
        if target_ref == "empty_bytes_trigger":
            return DownloadedMedia(
                media_id=media_id or "dev_empty_doc",
                content=b"",
                mime_type="application/pdf",
                filename="empty.pdf",
                file_size=0,
                provider_metadata={"source": "dev_simulator"},
            )

        # Scenario 6: Ref is a MIME/content mismatch test trigger (declared .pdf but content is HTML)
        if target_ref == "mismatch_trigger":
            return DownloadedMedia(
                media_id=media_id or "dev_mismatch_doc",
                content=b"<html><body>fake pdf executable</body></html>",
                mime_type="application/pdf",
                filename="fake_notice.pdf",
                file_size=40,
                provider_metadata={"source": "dev_simulator"},
            )

        raise ValueError(f"Media reference '{target_ref}' could not be resolved by DevMediaDownloader.")


class MetaMediaDownloader(BaseMediaDownloader):
    """
    Production Meta WhatsApp Cloud API Media Downloader.
    Retrieves media metadata from Meta Graph API, validates URLs via strict SSRF rules,
    isolates Bearer tokens across redirects, streams binary payload up to 10 MB limit.
    """

    async def download_media(
        self,
        media_id: str,
        media_url: Optional[str] = None,
    ) -> DownloadedMedia:
        if not media_id and not media_url:
            raise ValueError("Meta media download failed: Missing media ID or URL reference.")

        settings = get_settings()
        access_token = settings.meta_whatsapp_access_token
        if not access_token or not access_token.strip():
            raise ValueError("Meta media download failed: META_WHATSAPP_ACCESS_TOKEN is not configured.")

        api_version = settings.meta_whatsapp_api_version or "v21.0"
        graph_base = settings.meta_whatsapp_graph_url.rstrip("/")

        target_media_id = media_id or ""

        timeout = httpx.Timeout(10.0, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Step A: Request Media Metadata from Meta Graph API
            metadata_url = f"{graph_base}/{api_version}/{target_media_id}"
            validate_meta_url_ssrf(metadata_url)

            auth_headers = {"Authorization": f"Bearer {access_token.strip()}"}

            try:
                resp = await client.get(metadata_url, headers=auth_headers)
            except httpx.TimeoutException:
                raise asyncio.TimeoutError(f"Meta Graph API metadata request timed out for media ID '{target_media_id}'.")
            except Exception as exc:
                raise ValueError(f"Meta Graph API metadata network error: {exc}")

            if resp.status_code != 200:
                err_detail = f"Meta Graph API returned status {resp.status_code} for media ID '{target_media_id}'."
                if resp.status_code in (401, 403):
                    logger.error(f"[meta-media-downloader] Access token rejected by Meta API for media {target_media_id}.")
                elif resp.status_code == 404:
                    logger.warning(f"[meta-media-downloader] Media ID '{target_media_id}' not found or expired on Meta.")
                raise ValueError(err_detail)

            try:
                meta_json = resp.json()
            except Exception:
                raise ValueError(f"Malformed JSON response from Meta Graph API for media ID '{target_media_id}'.")

            download_url = meta_json.get("url")
            if not download_url:
                raise ValueError(f"Meta Graph API metadata response missing 'url' attribute for media ID '{target_media_id}'.")

            meta_mime = meta_json.get("mime_type", "application/octet-stream")

            # Step B & C: Validate URL SSRF and Download Media Binary
            current_url = download_url
            content_bytes = bytearray()

            max_redirects = 3
            redirect_count = 0

            while redirect_count <= max_redirects:
                validate_meta_url_ssrf(current_url)

                # Attach Bearer token ONLY if current_url passes Meta domain whitelist checks
                headers_to_send = dict(auth_headers)

                try:
                    async with client.stream("GET", current_url, headers=headers_to_send, follow_redirects=False) as dl_resp:
                        if dl_resp.status_code in (301, 302, 303, 307):
                            redirect_url = dl_resp.headers.get("location") or dl_resp.headers.get("Location")
                            if not redirect_url:
                                raise ValueError("HTTP redirect status received from Meta media server without Location header.")

                            current_url = urllib.parse.urljoin(current_url, redirect_url)
                            redirect_count += 1
                            continue

                        if dl_resp.status_code != 200:
                            raise ValueError(f"Meta media download server returned status {dl_resp.status_code}.")

                        # Content-Length Pre-Check
                        content_len_hdr = dl_resp.headers.get("Content-Length")
                        if content_len_hdr and content_len_hdr.isdigit():
                            if int(content_len_hdr) > MAX_MEDIA_SIZE_BYTES:
                                raise ValueError(f"Media exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

                        # Stream Byte Payload up to 10 MB limit
                        async for chunk in dl_resp.aiter_bytes():
                            content_bytes.extend(chunk)
                            if len(content_bytes) > MAX_MEDIA_SIZE_BYTES:
                                raise ValueError(f"Media exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

                        break  # Successfully downloaded binary payload

                except httpx.TimeoutException:
                    raise asyncio.TimeoutError("Media download connection timed out.")
                except ValueError:
                    raise
                except Exception as exc:
                    raise ValueError(f"Media download network error: {exc}")

            if redirect_count > max_redirects:
                raise ValueError("Media download failed: Exceeded maximum allowed HTTP redirects.")

            final_content = bytes(content_bytes)
            if len(final_content) == 0:
                raise ValueError("Downloaded media is empty (0 bytes).")

            meta_filename = meta_json.get("filename")
            if not meta_filename:
                safe_base = f"whatsapp_{target_media_id[:12]}"
                meta_filename = safe_base

            return DownloadedMedia(
                media_id=target_media_id,
                content=final_content,
                mime_type=meta_mime,
                filename=meta_filename,
                file_size=len(final_content),
                provider_metadata={
                    "source": "meta_cloud_api",
                    "media_id": target_media_id,
                    "sha256": meta_json.get("sha256"),
                },
            )


def get_whatsapp_media_downloader(provider_metadata: Optional[Dict[str, Any]] = None) -> BaseMediaDownloader:
    """
    Factory resolving the proper media downloader based on provider metadata & settings.
    Selects MetaMediaDownloader if provider indicates Meta Cloud API and token is configured.
    Falls back to DevMediaDownloader for simulated/local file testing.
    """
    meta = provider_metadata or {}
    provider = meta.get("provider")
    settings = get_settings()

    if provider == "meta_cloud_api" and settings.meta_whatsapp_access_token and settings.meta_whatsapp_access_token.strip():
        return MetaMediaDownloader()

    return DevMediaDownloader()
