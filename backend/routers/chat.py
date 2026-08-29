from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import json
import uuid

from cache import get_analysis, get_doc_text, set_doc_text
from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import answer_question_about_document
from services.gemini_service import detect_document_type, get_law_context
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()
settings = get_settings()


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

    # Use cached extracted text if available — avoids re-parsing the PDF on every question.
    doc_text = await get_doc_text(req.document_id)
    if not doc_text:
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
        await set_doc_text(req.document_id, doc_text, ttl=settings.redis_cache_ttl)

    # ── Grounding: document type + relevant Indian Acts ───────────────────────
    doc_type_key, doc_type_name = detect_document_type(doc_text, doc["filename"])
    law_context = get_law_context(doc_type_key)

    # ── Grounding: the document's saved analysis (precise type + key findings) ──
    analysis_summary = None
    cached = await get_analysis(req.document_id)
    if not cached:
        row = await db.fetchrow(
            "SELECT result_json FROM analyses WHERE document_id = $1", req.document_id
        )
        if row:
            try:
                cached = json.loads(row["result_json"])
            except (TypeError, ValueError):
                cached = None
    if isinstance(cached, dict):
        analysis_summary = cached.get("summary")
        if isinstance(analysis_summary, dict) and analysis_summary.get("document_type"):
            doc_type_name = analysis_summary["document_type"]

    # ── Grounding: recent conversation (fetched BEFORE inserting this message) ──
    hist_rows = await db.fetch(
        "SELECT role, content FROM chat_messages WHERE document_id = $1 ORDER BY timestamp DESC LIMIT 6",
        req.document_id,
    )
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(hist_rows)]

    user_msg_id = str(uuid.uuid4())
    user_now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO chat_messages (id, document_id, user_id, role, content, timestamp) VALUES ($1, $2, $3, 'user', $4, $5)",
        user_msg_id, req.document_id, current_user["id"], req.question, user_now,
    )

    try:
        answer = await answer_question_about_document(
            doc_text,
            req.question,
            doc_type_name=doc_type_name,
            law_context=law_context,
            analysis_summary=analysis_summary,
            history=history,
        )
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


class MultiChatRequest(BaseModel):
    document_ids: list[str]
    question: str


@router.post("/multi")
async def multi_document_chat(
    req: MultiChatRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Cross-document AI Q&A across multiple owned documents with attribution (SL-062).
    """
    if not req.document_ids:
        raise HTTPException(status_code=400, detail="Provide at least one document ID.")

    combined_sources = []
    for doc_id in req.document_ids[:5]:
        doc = await db.fetchrow("SELECT id, filename, user_id FROM documents WHERE id = $1", doc_id)
        if doc and doc["user_id"] == current_user["id"]:
            text = await get_doc_text(doc_id)
            if text:
                combined_sources.append(f"--- DOCUMENT [{doc['filename']}] (ID: {doc_id}) ---\n{text[:3000]}\n")

    if not combined_sources:
        raise HTTPException(status_code=404, detail="No readable documents found for multi-document Q&A.")

    context_str = "\n".join(combined_sources)
    answer = answer_question_about_document(context_str, req.question, "multi_document")

    return {
        "question": req.question,
        "answer": answer,
        "documents_queried": len(combined_sources),
    }

