"""
whatsapp_service.py — WhatsApp Legal Assistant Service Facade (SL-072).

Provides helper utilities and backward compatibility functions for outbound
WhatsApp messages and document analysis summary formatting.
"""

from typing import Dict, Any, List
from services.whatsapp.adapter import DevWhatsAppAdapter

_dev_adapter = DevWhatsAppAdapter()


def format_whatsapp_analysis_summary(
    document_name: str,
    risk_level: str,
    high_risk_count: int,
    key_obligations: List[str],
) -> str:
    """Format document analysis into WhatsApp markdown format."""
    obligations_text = (
        "\n".join([f"• {ob}" for ob in key_obligations[:3]])
        if key_obligations
        else "None noted."
    )

    return (
        f"📜 *SmartLegal AI Document Summary*\n"
        f"*Document:* {document_name}\n"
        f"*Overall Risk Level:* {risk_level.upper()}\n"
        f"*High Risk Warnings:* {high_risk_count} clause(s)\n\n"
        f"📌 *Key Signer Obligations:*\n{obligations_text}\n\n"
        f"⚖️ _SmartLegal AI provides automated information under Advocates Act 1961 guidelines._"
    )


def send_whatsapp_message(phone_number: str, message: str) -> Dict[str, Any]:
    """Dispatch WhatsApp message using dev adapter."""
    return _dev_adapter.send_outbound_message(phone_number, message)
