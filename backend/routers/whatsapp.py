from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.whatsapp_service import format_whatsapp_analysis_summary, send_whatsapp_message
from routers.auth import get_current_user

router = APIRouter()


class WhatsAppShareRequest(BaseModel):
    phone_number: str
    document_name: str
    risk_level: str
    high_risk_count: int
    obligations: list[str] = []


@router.post("/send-summary")
async def send_summary_to_whatsapp(
    req: WhatsAppShareRequest,
    current_user=Depends(get_current_user),
):
    """Send document analysis summary to WhatsApp (SL-072)."""
    if not req.phone_number:
        raise HTTPException(status_code=400, detail="Mobile phone number required.")

    formatted_msg = format_whatsapp_analysis_summary(
        req.document_name, req.risk_level, req.high_risk_count, req.obligations
    )
    result = send_whatsapp_message(req.phone_number, formatted_msg)
    return {"message": "WhatsApp summary queued successfully.", "details": result}
