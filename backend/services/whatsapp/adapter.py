"""
adapter.py — WhatsApp Channel Provider Adapter Interface & Dev Implementation.

Isolates provider-specific WhatsApp APIs (Meta Graph API, Twilio, Dev Simulator)
from SmartLegal AI core business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from schemas.whatsapp import InboundMessagePayload, OutboundMessagePayload


class BaseWhatsAppAdapter(ABC):
    """Abstract interface for WhatsApp channel providers."""

    @abstractmethod
    def parse_inbound_payload(self, raw_payload: Dict[str, Any]) -> InboundMessagePayload:
        """Parse raw incoming HTTP payload into normalized InboundMessagePayload."""
        pass

    @abstractmethod
    def send_outbound_message(self, to_phone: str, message_text: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """Dispatch outbound WhatsApp message."""
        pass


class DevWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    Development/Simulation adapter.
    Handles normalized test payloads without calling external provider APIs.
    """

    def parse_inbound_payload(self, raw_payload: Dict[str, Any]) -> InboundMessagePayload:
        """Normalize development simulated payload."""
        if isinstance(raw_payload, InboundMessagePayload):
            return raw_payload

        return InboundMessagePayload(
            from_phone=raw_payload.get("from_phone", raw_payload.get("phone", "")),
            message_text=raw_payload.get("message_text", raw_payload.get("text", "")),
            message_id=raw_payload.get("message_id"),
            message_type=raw_payload.get("message_type", "text"),
            media_url=raw_payload.get("media_url"),
            timestamp=raw_payload.get("timestamp"),
        )

    def send_outbound_message(self, to_phone: str, message_text: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """Simulate sending an outbound message."""
        outbound = OutboundMessagePayload(
            to_phone=to_phone,
            message_text=message_text,
            media_url=media_url,
        )
        print(f"[DevWhatsAppAdapter] Outbound message to {to_phone}:\n{message_text}\n")
        return {
            "status": "queued",
            "provider": "dev_simulator",
            "recipient": outbound.to_phone,
            "message_length": len(outbound.message_text),
            "has_media": bool(outbound.media_url),
        }
