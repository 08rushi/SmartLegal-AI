from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

from database import get_db
from services.gemini_service import answer_question_about_document
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()


class ChatRequest(BaseModel):
    document_id: str
    question: str


@router.post("")
async def chat(
    req: ChatRequest,
    db=Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM documents WHERE id = ?",
        (req.document_id,),
    ) as cur:
        doc = await cur.fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_url = doc["file_url"]
    try:
        if file_url.startswith("local://"):
            local_path = file_url.replace("local://", "")
            with open(local_path, "rb") as f:
                file_bytes = f.read()
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url)
                file_bytes = resp.content

        doc_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read document: {str(e)}")

    try:
        answer = await answer_question_about_document(doc_text, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI failed to answer: {str(e)}")

    ai_msg_id = str(uuid.uuid4())
    ai_now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO chat_messages (id, document_id, user_id, role, content, timestamp) VALUES (?, ?, ?, 'assistant', ?, ?)",
        (ai_msg_id, req.document_id, "anonymous", answer, ai_now),
    )
    await db.commit()

    return {
        "message": {
            "id": ai_msg_id,
            "role": "assistant",
            "content": answer,
            "timestamp": ai_now,
        }
    }


@router.get("/{document_id}/history")
async def get_chat_history(
    document_id: str,
    db=Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM chat_messages WHERE document_id = ? ORDER BY timestamp ASC",
        (document_id,),
    ) as cur:
        rows = await cur.fetchall()
    return {"messages": [dict(r) for r in rows]}