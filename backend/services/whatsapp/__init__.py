"""
whatsapp package — Decoupled WhatsApp Bot module.

Architecture:
WhatsApp Channel -> WhatsApp Adapter -> Conversation/Orchestration Layer -> SmartLegal Services
"""

from services.whatsapp.adapter import BaseWhatsAppAdapter, DevWhatsAppAdapter
from services.whatsapp.meta_adapter import MetaWhatsAppAdapter, normalize_phone_number
from services.whatsapp.orchestrator import WhatsAppOrchestrator

__all__ = [
    "BaseWhatsAppAdapter",
    "DevWhatsAppAdapter",
    "MetaWhatsAppAdapter",
    "normalize_phone_number",
    "WhatsAppOrchestrator",
]
