from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
import json
import logging
import uuid

from cache import get_analysis, get_doc_text, set_doc_text
from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import answer_question_about_document
from services.gemini_service import detect_document_type, get_law_context
from services.pdf_parser import extract_text_from_pdf_str
from services.retrieval import select_relevant_text
from services.lang import resolve_lang
from services import storage

router = APIRouter()
settings = get_settings()


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    document_id: str
    question: str = Field(..., min_length=1, max_length=4000)
    lang: str | None = Field(default=None, description="mr | hi | en (falls back to X-Lang header, then en)")


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
            file_bytes = await storage.read_document_bytes(file_url)
            doc_text = extract_text_from_pdf_str(file_bytes)
        except Exception as e:
            logger.exception("[chat] could not read document %s: %s", req.document_id, type(e).__name__)
            raise HTTPException(status_code=500, detail="Could not read the document. Please try again.")
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

    lang = resolve_lang(request, req.lang)
    try:
        answer = await answer_question_about_document(
            # Long documents: send the opening + the pages that match the question, not just the first 12K chars.
            select_relevant_text(doc_text, req.question),
            req.question,
            doc_type_name=doc_type_name,
            law_context=law_context,
            analysis_summary=analysis_summary,
            history=history,
            lang=lang,
        )
    except Exception as e:
        logger.exception("[chat] AI answer failed for document %s: %s", req.document_id, type(e).__name__)
        raise HTTPException(status_code=500, detail="The AI could not answer right now. Please try again.")

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
    document_ids: list[str] = Field(..., min_length=1, max_length=5)
    question: str = Field(..., min_length=1, max_length=4000)
    lang: str | None = Field(default=None, description="mr | hi | en (falls back to X-Lang header, then en)")


@router.post("/multi")
@limiter.limit("20/minute")
async def multi_document_chat(
    request: Request,
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
        doc = await db.fetchrow("SELECT id, filename, user_id, file_url FROM documents WHERE id = $1", doc_id)
        if doc and doc["user_id"] == current_user["id"]:
            text = await get_doc_text(doc_id)
            if not text:
                try:
                    file_bytes = await storage.read_document_bytes(doc["file_url"])
                    text = extract_text_from_pdf_str(file_bytes)
                    await set_doc_text(doc_id, text, ttl=settings.redis_cache_ttl)
                except Exception as exc:
                    logger.warning("[chat/multi] could not read document %s: %s", doc_id, type(exc).__name__)
                    text = ""
            if text:
                combined_sources.append(f"--- DOCUMENT [{doc['filename']}] (ID: {doc_id}) ---\n{text[:3000]}\n")

    if not combined_sources:
        raise HTTPException(status_code=404, detail="No readable documents found for multi-document Q&A.")

    context_str = "\n".join(combined_sources)
    try:
        answer = await answer_question_about_document(
            context_str, req.question, doc_type_name="multiple documents",
            lang=resolve_lang(request, req.lang),
        )
    except Exception as exc:
        logger.exception("[chat/multi] AI answer failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="The AI could not answer right now. Please try again.")

    return {
        "question": req.question,
        "answer": answer,
        "documents_queried": len(combined_sources),
    }

