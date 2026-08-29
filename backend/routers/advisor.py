"""
Virtual Legal Advisor — general Indian-law consultation.

Unlike /chat (which answers questions about a specific uploaded document), this
endpoint acts as an experienced Indian advocate the user can consult about any
legal problem: a contract they are about to sign, a case they want to file, which
Articles/Acts strengthen their position, their chances of success, and so on.

The conversation is stateless on the server — the client sends recent history with
each turn — so no new database table is required.
"""

from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import get_legal_advice

router = APIRouter()


class AdvisorTurn(BaseModel):
    role: str
    content: str


class AdvisorRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=6000)
    history: list[AdvisorTurn] = Field(default_factory=list)


@router.post("")
@limiter.limit("15/minute")
async def ask_advisor(
    request: Request,
    req: AdvisorRequest,
    current_user=Depends(get_current_user),
):
    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please describe your legal question.")

    # Keep only the most recent turns to bound the prompt size.
    history = [{"role": t.role, "content": t.content} for t in req.history][-12:]

    try:
        answer = await get_legal_advice(question, history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Advisor failed to answer: {exc}")

    return {
        "message": {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": answer,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
