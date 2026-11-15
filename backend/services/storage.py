"""
Private document storage helpers.

Uploaded documents live in Cloudinary as *authenticated* (private) raw assets, so the
stored URL alone is useless: every read goes through a short-lived signed URL that is
only generated server-side after an ownership check. Legacy assets uploaded as public
("upload" delivery type) are still readable until scripts/migrate_cloudinary_to_private.py
has been applied.

Server-side fetches of a stored ``file_url`` MUST use ``read_document_bytes`` so that
(1) private assets are fetched through the signed API URL and (2) only Cloudinary hosts
for *our* cloud are ever requested (no SSRF via a tampered DB row).
"""
from __future__ import annotations

import re
import time
from urllib.parse import unquote, urlparse

from config import get_settings

settings = get_settings()

SIGNED_URL_TTL_SECONDS = 300  # ~5 minutes
_ALLOWED_HOSTS = {"res.cloudinary.com", "api.cloudinary.com"}

_CLOUD_URL_RE = re.compile(
    r"^https://res\.cloudinary\.com/(?P<cloud>[^/]+)/(?P<rtype>raw|image|video)/"
    r"(?P<dtype>upload|authenticated|private)/(?:s--[^/]+--/)?(?:v\d+/)?(?P<pid>.+?)(?:\?.*)?$"
)


class StorageError(Exception):
    """Raised when a stored file reference is unusable or points somewhere not allowed."""


def parse_cloudinary_url(url: str | None) -> dict | None:
    """Parse a Cloudinary delivery URL -> {cloud, resource_type, type, public_id} or None."""
    m = _CLOUD_URL_RE.match(url or "")
    if not m:
        return None
    return {
        "cloud": m.group("cloud"),
        "resource_type": m.group("rtype"),
        "type": m.group("dtype"),
        "public_id": unquote(m.group("pid")),
    }


def is_allowed_cloud_url(url: str | None) -> bool:
    """True only for https Cloudinary URLs that belong to the configured cloud."""
    try:
        host = (urlparse(url or "").hostname or "").lower()
    except ValueError:
        return False
    if host not in _ALLOWED_HOSTS or not (url or "").startswith("https://"):
        return False
    parsed = parse_cloudinary_url(url)
    if parsed is None:
        return False
    expected = (settings.cloudinary_cloud_name or "").strip()
    return bool(expected) and parsed["cloud"] == expected


def _configure() -> None:
    import cloudinary
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def signed_download_url(file_url: str, ttl_seconds: int = SIGNED_URL_TTL_SECONDS) -> str:
    """
    Short-lived signed URL for a stored Cloudinary asset. Private (authenticated) assets
    get an API download URL that expires after ``ttl_seconds``; legacy public assets are
    returned unchanged (after the host allow-check).
    """
    if not is_allowed_cloud_url(file_url):
        raise StorageError("File location is not an allowed storage URL.")
    info = parse_cloudinary_url(file_url)
    if info["type"] == "upload":
        return file_url  # legacy public asset; migrate with the migration script
    _configure()
    from cloudinary.utils import private_download_url
    return private_download_url(
        info["public_id"],
        "",
        resource_type=info["resource_type"],
        type=info["type"],
        expires_at=int(time.time()) + int(ttl_seconds),
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )


async def read_document_bytes(file_url: str) -> bytes:
    """
    Read a stored document: ``local://`` paths (dev only) or Cloudinary (private/legacy).
    Raises FileNotFoundError for a missing local file, StorageError for a disallowed URL
    and httpx.HTTPStatusError for a failed remote fetch.
    """
    file_url = file_url or ""
    if file_url.startswith("local://"):
        with open(file_url[len("local://"):], "rb") as f:
            return f.read()

    url = signed_download_url(file_url, ttl_seconds=60)
    if urlparse(url).hostname not in _ALLOWED_HOSTS:  # defence in depth
        raise StorageError("File location is not an allowed storage URL.")
    import httpx
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
