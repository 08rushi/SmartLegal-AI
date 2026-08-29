"""
whatsapp_service.py — WhatsApp Legal Assistant Service (SL-072).

Formats and delivers document analysis summaries, risk warnings, and civic application
reminders directly to Indian citizens via WhatsApp.
"""

from typing import Dict, Any


def format_whatsapp_analysis_summary(document_name: str, risk_level: str, high_risk_count: int, key_obligations: list[str]) -> str:
    """Format document analysis into WhatsApp markdown format."""
    obligations_text = "\n".join([f"• {ob}" for ob in key_obligations[:3]]) if key_obligations else "None noted."

    return (
        f"📜 *SmartLegal AI Document Summary*\n"
        f"*Document:* {document_name}\n"
        f"*Overall Risk Level:* {risk_level.upper()}\n"
        f"*High Risk Warnings:* {high_risk_count} clause(s)\n\n"
        f"📌 *Key Signer Obligations:*\n{obligations_text}\n\n"
        f"⚖️ _SmartLegal AI provides automated information under Advocates Act 1961 guidelines._"
    )


def send_whatsapp_message(phone_number: str, message: str) -> Dict[str, Any]:
    """Mock/Production WhatsApp API dispatcher."""
    print(f"[WhatsApp Dispatch] Sending to {phone_number}:\n{message}\n")
    return {
        "status": "queued",
        "recipient": phone_number,
        "message_length": len(message),
    }
