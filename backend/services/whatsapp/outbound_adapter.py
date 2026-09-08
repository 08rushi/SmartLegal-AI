"""
outbound_adapter.py — Meta WhatsApp Cloud API & Dev Simulator Outbound Adapters.

Enforces:
1. Provider-neutral BaseWhatsAppOutboundAdapter interface.
2. Meta Cloud API text message dispatch (POST /{phone_number_id}/messages).
3. Recipient phone E.164 normalization (+91... -> 91...).
4. Bearer token security isolation (token masked in all logs and exception messages).
5. Explicit HTTP timeout (10s) and status error classification (4xx non-retryable vs 5xx retryable).
"""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
import json
import logging
import uuid
from typing import Optional, Dict, Any

import httpx

from config import get_settings
from services.whatsapp.meta_adapter import normalize_phone_number

logger = logging.getLogger(__name__)


@dataclass
class OutboundSendResult:
    """Normalized result returned by outbound adapters."""

    success: bool
    delivery_status: str  # 'sent', 'failed_retryable', 'failed_non_retryable', 'unknown'
    provider_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 1


class BaseWhatsAppOutboundAdapter(ABC):
    """Abstract provider boundary for sending WhatsApp outbound messages."""

    @abstractmethod
    async def send_text_message(
        self,
        recipient_phone: str,
        message_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OutboundSendResult:
        """Send outbound text message to target recipient."""
        pass


class DevWhatsAppOutboundAdapter(BaseWhatsAppOutboundAdapter):
    """Development Simulator Outbound Adapter (0 network calls)."""

    async def send_text_message(
        self,
        recipient_phone: str,
        message_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OutboundSendResult:
        normalized_to = normalize_phone_number(recipient_phone)
        mock_wamid = f"dev_out_{uuid.uuid4().hex[:12]}"
        logger.info(f"[dev-outbound-adapter] Simulated send to {normalized_to}: {message_text[:40]}...")
        return OutboundSendResult(
            success=True,
            delivery_status="sent",
            provider_message_id=mock_wamid,
            attempt_count=1,
        )


class MetaWhatsAppOutboundAdapter(BaseWhatsAppOutboundAdapter):
    """Production Meta WhatsApp Cloud API Outbound Adapter."""

    async def send_text_message(
        self,
        recipient_phone: str,
        message_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OutboundSendResult:
        settings = get_settings()
        access_token = settings.meta_whatsapp_access_token
        phone_number_id = settings.meta_whatsapp_phone_number_id

        if not access_token or not access_token.strip():
            logger.error("[meta-outbound-adapter] META_WHATSAPP_ACCESS_TOKEN is not configured.")
            return OutboundSendResult(
                success=False,
                delivery_status="failed_non_retryable",
                error_code="MISSING_TOKEN",
                error_message="META_WHATSAPP_ACCESS_TOKEN is not configured.",
                attempt_count=1,
            )

        if not phone_number_id or not phone_number_id.strip():
            logger.error("[meta-outbound-adapter] META_WHATSAPP_PHONE_NUMBER_ID is not configured.")
            return OutboundSendResult(
                success=False,
                delivery_status="failed_non_retryable",
                error_code="MISSING_PHONE_NUMBER_ID",
                error_message="META_WHATSAPP_PHONE_NUMBER_ID is not configured.",
                attempt_count=1,
            )

        api_version = settings.meta_whatsapp_api_version or "v21.0"
        graph_base = settings.meta_whatsapp_graph_url.rstrip("/")

        target_url = f"{graph_base}/{api_version}/{phone_number_id.strip()}/messages"
        clean_phone = normalize_phone_number(recipient_phone).lstrip("+")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }

        token_clean = access_token.strip()
        headers = {
            "Authorization": f"Bearer {token_clean}",
            "Content-Type": "application/json",
        }

        timeout = httpx.Timeout(10.0, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(target_url, json=payload, headers=headers)
        except (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError):
            logger.warning(f"[meta-outbound-adapter] Network timeout posting outbound message to recipient {clean_phone}.")
            return OutboundSendResult(
                success=False,
                delivery_status="unknown",
                error_code="NETWORK_TIMEOUT_UNKNOWN",
                error_message="Request transmitted but connection timed out before Meta HTTP response.",
                attempt_count=1,
            )
        except Exception as exc:
            logger.warning(f"[meta-outbound-adapter] Network error posting outbound message: {exc}")
            return OutboundSendResult(
                success=False,
                delivery_status="failed_retryable",
                error_code="NETWORK_ERROR",
                error_message=f"Network error: {type(exc).__name__}",
                attempt_count=1,
            )

        if resp.status_code in (200, 201):
            try:
                res_json = resp.json()
                messages = res_json.get("messages", [])
                wamid = messages[0].get("id") if messages else None
                if not wamid:
                    wamid = f"meta_out_{uuid.uuid4().hex[:12]}"
                return OutboundSendResult(
                    success=True,
                    delivery_status="sent",
                    provider_message_id=wamid,
                    attempt_count=1,
                )
            except Exception as json_exc:
                logger.error(f"[meta-outbound-adapter] Malformed JSON response from Meta: {json_exc}")
                return OutboundSendResult(
                    success=False,
                    delivery_status="failed_retryable",
                    error_code="MALFORMED_JSON",
                    error_message="Meta API returned invalid JSON payload.",
                    attempt_count=1,
                )

        # Handle Non-200 HTTP Errors
        status_code = resp.status_code
        err_code_str = str(status_code)

        try:
            err_json = resp.json()
            error_obj = err_json.get("error", {})
            err_msg = error_obj.get("message", f"HTTP {status_code}")
        except Exception:
            err_msg = f"HTTP {status_code} Error"

        clean_err_msg = err_msg.replace(token_clean, "[MASKED_TOKEN]")

        if 400 <= status_code < 500:
            logger.warning(f"[meta-outbound-adapter] Non-retryable Meta 4xx error ({status_code}): {clean_err_msg}")
            return OutboundSendResult(
                success=False,
                delivery_status="failed_non_retryable",
                error_code=err_code_str,
                error_message=clean_err_msg,
                attempt_count=1,
            )

        logger.warning(f"[meta-outbound-adapter] Retryable Meta 5xx error ({status_code}): {clean_err_msg}")
        return OutboundSendResult(
            success=False,
            delivery_status="failed_retryable",
            error_code=err_code_str,
            error_message=clean_err_msg,
            attempt_count=1,
        )


def get_whatsapp_outbound_adapter(provider: Optional[str] = None) -> BaseWhatsAppOutboundAdapter:
    """Factory resolving outbound adapter based on provider metadata & settings."""
    settings = get_settings()
    if (
        provider == "meta_cloud_api"
        and settings.meta_whatsapp_access_token
        and settings.meta_whatsapp_access_token.strip()
        and settings.meta_whatsapp_phone_number_id
        and settings.meta_whatsapp_phone_number_id.strip()
    ):
        return MetaWhatsAppOutboundAdapter()
    return DevWhatsAppOutboundAdapter()
