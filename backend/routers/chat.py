from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import uuid

from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import answer_question_about_document
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()


class ChatRequest(BaseModel):
    document_id: str
    question: str


@router.post("")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    req: ChatRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = await db.fetchrow(
        "SELECT * FROM documents WHERE id = $1",
        req.document_id,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to chat on this document.")

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

    user_msg_id = str(uuid.uuid4())
    user_now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO chat_messages (id, document_id, user_id, role, content, timestamp) VALUES ($1, $2, $3, 'user', $4, $5)",
        user_msg_id, req.document_id, current_user["id"], req.question, user_now,
    )

    try:
        answer = await answer_question_about_document(doc_text, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI failed to answer: {str(e)}")

    ai_msg_id = str(uuid.uuid4())
    ai_now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO chat_messages (id, document_id, user_id, role, content, timestamp) VALUES ($1, $2, $3, 'assistant', $4, $5)",
        ai_msg_id, req.document_id, current_user["id"], answer, ai_now,
    )

    return {
        "user_message": {
            "id": user_msg_id,
            "role": "user",
            "content": req.question,
            "timestamp": user_now,
        },
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
    current_user=Depends(get_current_user),
):
    doc = await db.fetchrow(
        "SELECT user_id FROM documents WHERE id = $1", document_id
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to access this document's chat history.")

    rows = await db.fetch(
        "SELECT * FROM chat_messages WHERE document_id = $1 ORDER BY timestamp ASC",
        document_id,
    )
    return {"messages": [dict(r) for r in rows]}
