"""
whatsapp.py — Pydantic schemas for WhatsApp bot interaction and summary sharing.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class InboundMessagePayload(BaseModel):
    """Normalized payload for an incoming WhatsApp message."""

    from_phone: str = Field(..., description="Sender phone number in E.164 format, e.g., +919876543210")
    message_text: str = Field(..., description="Text message body sent by the user")
    message_id: Optional[str] = Field(None, description="Unique provider message ID")
    message_type: Optional[str] = Field("text", description="Type of message (text, image, document, location, etc.)")
    media_url: Optional[str] = Field(None, description="URL of attached media/document if present")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of the message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider metadata (media_id, mime_type, filename, phone_number_id, etc.)")


class OutboundMessagePayload(BaseModel):
    """Normalized payload for an outgoing WhatsApp message."""

    to_phone: str = Field(..., description="Recipient phone number in E.164 format")
    message_text: str = Field(..., description="Formatted text message to be delivered")
    media_url: Optional[str] = Field(None, description="Optional media URL attachment")


class SimulatedMessageResponse(BaseModel):
    """Response format for simulated inbound WhatsApp messages (Dev API)."""

    status: str = Field("ok", description="Status of message processing")
    received: InboundMessagePayload = Field(..., description="The parsed inbound payload")
    reply: Optional[str] = Field(None, description="Generated response message")
    processed_at: str = Field(..., description="ISO 8601 timestamp of execution")


class WhatsAppShareRequest(BaseModel):
    """Request model for sending analysis summary via WhatsApp (SL-072)."""

    phone_number: str = Field(..., description="Recipient phone number")
    document_name: str = Field(..., description="Name of analyzed document")
    risk_level: str = Field(..., description="Overall document risk rating")
    high_risk_count: int = Field(..., description="Count of high risk clauses")
    obligations: List[str] = Field(default_factory=list, description="Key obligations summary")


class WhatsAppShareResponse(BaseModel):
    """Response model for document summary delivery queueing."""

    message: str
    details: Dict[str, Any]
