"""
meta_adapter.py — Meta WhatsApp Cloud API Channel Provider Adapter.

Isolates Meta Cloud API Webhook payload normalization, multi-message extraction,
E.164 phone normalization, status event filtering, and outbound message stubs.
"""

import datetime
import re
from typing import Dict, Any, List, Optional
from schemas.whatsapp import InboundMessagePayload, OutboundMessagePayload
from services.whatsapp.adapter import BaseWhatsAppAdapter


def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalize raw phone number string to E.164 format (+919876543210).
    Meta webhooks send phone numbers without leading '+' (e.g. '919876543210').
    """
    if not raw_phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.isdigit() and len(cleaned) >= 10:
        return f"+{cleaned}"
    return cleaned


class MetaWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    Production Meta WhatsApp Cloud API Channel Adapter.
    Handles Meta Graph API Webhook payload structure.
    """

    def parse_inbound_payload(self, raw_payload: Dict[str, Any]) -> InboundMessagePayload:
        """
        Single-message adapter compatibility implementation.
        Accepts normalized InboundMessagePayload object/dict or parses raw Meta webhook JSON.
        Raises ValueError if payload contains no valid user messages (e.g. status events).
        """
        if isinstance(raw_payload, InboundMessagePayload):
            return raw_payload

        if isinstance(raw_payload, dict) and "from_phone" in raw_payload and "object" not in raw_payload:
            return InboundMessagePayload(**raw_payload)

        payloads = self.extract_inbound_payloads(raw_payload)
        if not payloads:
            raise ValueError("Payload contains no inbound user messages (status event or empty payload).")
        return payloads[0]

    def extract_inbound_payloads(self, raw_payload: Dict[str, Any]) -> List[InboundMessagePayload]:
        """
        Extract and normalize all inbound user messages from a Meta webhook payload.
        Handles batched messages (1 or N) and filters out status/read/delivery events cleanly.
        """
        if not isinstance(raw_payload, dict):
            raise ValueError("Malformed Meta webhook payload: expected JSON object.")

        # Top-level object verification
        obj_type = raw_payload.get("object")
        if obj_type != "whatsapp_business_account":
            raise ValueError(f"Invalid webhook object type: '{obj_type}'. Expected 'whatsapp_business_account'.")

        entries = raw_payload.get("entry")
        if not isinstance(entries, list) or not entries:
            return []

        normalized_messages: List[InboundMessagePayload] = []

        for entry in entries:
            changes = entry.get("changes") if isinstance(entry, dict) else None
            if not isinstance(changes, list):
                continue

            for change in changes:
                value = change.get("value") if isinstance(change, dict) else None
                if not isinstance(value, dict):
                    continue

                # Status notifications (sent, delivered, read) do not contain user messages
                if "statuses" in value and "messages" not in value:
                    continue

                messages = value.get("messages")
                if not isinstance(messages, list) or not messages:
                    continue

                metadata_obj = value.get("metadata", {})
                phone_number_id = metadata_obj.get("phone_number_id")

                for msg in messages:
                    if not isinstance(msg, dict):
                        continue

                    msg_id = msg.get("id")
                    if not msg_id or not str(msg_id).strip():
                        continue

                    from_phone_raw = msg.get("from", "")
                    from_phone = normalize_phone_number(from_phone_raw)
                    msg_type = msg.get("type", "text")

                    # Convert Unix epoch timestamp seconds to ISO 8601 UTC string
                    raw_ts = msg.get("timestamp")
                    iso_ts = None
                    if raw_ts:
                        try:
                            ts_int = int(raw_ts)
                            iso_ts = datetime.datetime.fromtimestamp(ts_int, tz=datetime.timezone.utc).isoformat()
                        except Exception:
                            iso_ts = str(raw_ts)

                    # Content extraction based on message type
                    message_text = ""
                    media_id = None
                    mime_type = None
                    filename = None
                    caption = None

                    if msg_type == "text":
                        text_obj = msg.get("text", {})
                        message_text = text_obj.get("body", "") if isinstance(text_obj, dict) else ""
                    elif msg_type in ("image", "document", "audio", "video", "sticker"):
                        media_obj = msg.get(msg_type, {})
                        if isinstance(media_obj, dict):
                            media_id = media_obj.get("id")
                            mime_type = media_obj.get("mime_type")
                            filename = media_obj.get("filename")
                            caption = media_obj.get("caption")
                        message_text = caption or f"[{msg_type.capitalize()} attached]"
                    elif msg_type == "location":
                        loc_obj = msg.get("location", {})
                        if isinstance(loc_obj, dict):
                            message_text = f"Location: lat={loc_obj.get('latitude')}, long={loc_obj.get('longitude')}"
                    else:
                        message_text = f"[{msg_type.capitalize()} message]"

                    # Assemble provider metadata dict
                    provider_meta = {
                        "provider": "meta_cloud_api",
                        "phone_number_id": phone_number_id,
                        "media_id": media_id,
                        "mime_type": mime_type,
                        "filename": filename,
                        "caption": caption,
                    }

                    inbound = InboundMessagePayload(
                        from_phone=from_phone,
                        message_text=message_text,
                        message_id=msg_id,
                        message_type=msg_type,
                        media_url=None,  # Preserved media_id in metadata for Step 3B downloader
                        timestamp=iso_ts,
                        metadata=provider_meta,
                    )
                    normalized_messages.append(inbound)

        return normalized_messages

    def send_outbound_message(self, to_phone: str, message_text: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Outbound Meta Graph API message stub (Step 3C readiness).
        """
        outbound = OutboundMessagePayload(
            to_phone=to_phone,
            message_text=message_text,
            media_url=media_url,
        )
        return {
            "status": "prepared",
            "provider": "meta_cloud_api",
            "recipient": outbound.to_phone,
            "message_length": len(outbound.message_text),
            "has_media": bool(outbound.media_url),
        }
