"""Transactional email via Resend. Never raises; never logs tokens or bodies."""
import html
import logging
from urllib.parse import quote

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def email_configured() -> bool:
    s = get_settings()
    return bool(s.resend_api_key.strip() and s.email_from.strip())


def build_reset_link(token: str) -> str:
    base = get_settings().frontend_url.rstrip("/")
    return f"{base}/reset-password?token={quote(token, safe='')}"


async def send_email(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send via Resend. Returns True on success, False otherwise (never raises)."""
    s = get_settings()
    if not email_configured():
        return False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {s.resend_api_key}"},
                json={"from": s.email_from, "to": [to], "subject": subject,
                      "html": html_body, "text": text_body},
            )
        if resp.status_code >= 300:
            logger.warning("Resend email failed: HTTP %s", resp.status_code)
            return False
        return True
    except Exception as exc:  # noqa: BLE001 - must never break the caller
        logger.warning("Resend email error: %s", type(exc).__name__)
        return False


async def send_password_reset_email(to: str, token: str, expires_minutes: int) -> bool:
    link = build_reset_link(token)
    subject = "Reset your SmartLegal AI password"
    text = (
        f"We received a request to reset your SmartLegal AI password.\n\n"
        f"Open this link to choose a new password (valid for {expires_minutes} minutes):\n{link}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "आपका पासवर्ड रीसेट करने के लिए ऊपर दिए गए लिंक का उपयोग करें। यदि आपने अनुरोध नहीं किया, तो इसे अनदेखा करें।\n"
        "तुमचा पासवर्ड रीसेट करण्यासाठी वरील लिंक वापरा. तुम्ही विनंती केली नसल्यास हा ईमेल दुर्लक्षित करा.\n"
    )
    safe = html.escape(link, quote=True)
    body = (
        "<p>We received a request to reset your SmartLegal AI password.</p>"
        f'<p><a href="{safe}">Reset your password</a> (valid for {expires_minutes} minutes)</p>'
        "<p>If you did not request this, you can ignore this email.</p>"
        "<p>आपका पासवर्ड रीसेट करने के लिए ऊपर दिए गए लिंक का उपयोग करें। यदि आपने अनुरोध नहीं किया, तो इसे अनदेखा करें।</p>"
        "<p>तुमचा पासवर्ड रीसेट करण्यासाठी वरील लिंक वापरा. तुम्ही विनंती केली नसल्यास हा ईमेल दुर्लक्षित करा.</p>"
    )
    return await send_email(to, subject, body, text)
