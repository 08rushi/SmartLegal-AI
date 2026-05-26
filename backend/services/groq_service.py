"""
Groq AI service fallback for PDF text analysis.

Provider: Groq (llama-3.3-70b-versatile)
Text-only: No image support. Used as fallback when Gemini is rate-limited.
"""

import json
import asyncio
from typing import Union

from groq import Groq
from config import get_settings

settings = get_settings()

# ── Client Setup ──────────────────────────────────────────────────────────────

_groq_client: Union[Groq, None] = None


def _get_groq_client() -> Groq:
    """Get or create Groq client (lazy init)."""
    global _groq_client
    if _groq_client is None:
        api_key = settings.groq_api_key
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured in backend/.env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Reuse Gemini Service Helpers ──────────────────────────────────────────────

from services.gemini_service import (
    DOCUMENT_TEMPLATES,
    detect_document_type,
    get_law_context,
    _extract_json,
    _build_fallback_summary,
    _chunk_prompt,
    _summary_prompt,
    _chat_prompt,
)


# ── Groq API Calls ───────────────────────────────────────────────────────────

async def _call_groq(prompt: str, max_tokens: int = 4000) -> str:
    """Call Groq API synchronously (wrapped in async)."""
    loop = asyncio.get_event_loop()

    def _sync_call():
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    return await loop.run_in_executor(None, _sync_call)


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze_legal_document(text: str, filename: str) -> dict:
    """
    Analyze a legal document text using Groq (text-only, PDFs only).

    Args:
        text: Extracted PDF text with page markers
        filename: Original filename for type detection

    Returns:
        {summary, clauses} with same schema
    """
    doc_type, doc_type_name = detect_document_type(text, filename)
    law_context = get_law_context(doc_type)

    print(f"[groq] Detected document type: {doc_type} ({doc_type_name}) for '{filename}'")

    from services.pdf_parser import split_into_chunks

    chunks = split_into_chunks(text, max_chars=12000)
    print(f"[groq] Split text into {len(chunks)} chunks")

    all_clauses = []
    chunk_errors = []

    if not chunks:
        raise RuntimeError("Groq analysis failed: no text chunks were available.")

    for i, chunk in enumerate(chunks):
        prompt = _chunk_prompt(doc_type_name, law_context, chunk["text"], i)
        try:
            raw = await _call_groq(prompt, max_tokens=4000)
            parsed = _extract_json(raw)

            if isinstance(parsed, list):
                for clause in parsed:
                    clause.setdefault("page_number", chunk.get("start_page", 1))
                    clause.setdefault("chunk_index", i)
                    if clause.get("risk_level") not in ("low", "medium", "high"):
                        clause["risk_level"] = "medium"
                    try:
                        score = int(clause.get("risk_score", 5))
                        clause["risk_score"] = max(1, min(10, score))
                    except (ValueError, TypeError):
                        clause["risk_score"] = 5
                all_clauses.extend(parsed)
                print(f"[groq] Chunk {i + 1} done: {len(parsed)} clauses extracted")
            else:
                msg = f"Chunk {i + 1}: unexpected response shape {type(parsed).__name__}"
                chunk_errors.append(msg)
                print(f"[groq] {msg}, skipping")

        except Exception as exc:
            msg = f"Chunk {i + 1} failed: {exc}"
            chunk_errors.append(msg)
            print(f"[groq] {msg}")

    if not all_clauses:
        reason = "; ".join(chunk_errors[:3]) if chunk_errors else "model returned empty clause arrays"
        raise RuntimeError(f"Groq extracted zero clauses from readable text. {reason}")

    # ── Summary ───────────────────────────────────────────────────────────────
    summary_prompt = _summary_prompt(
        doc_type_name, law_context, json.dumps(all_clauses[:20], indent=2)
    )
    try:
        raw_summary = await _call_groq(summary_prompt, max_tokens=2000)
        summary = _extract_json(raw_summary)
        summary["total_clauses"] = len(all_clauses)
        summary["high_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "high")
        summary["medium_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
        summary["low_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "low")
    except Exception as exc:
        print(f"[groq] Summary failed: {exc}")
        summary = _build_fallback_summary(doc_type_name, all_clauses)

    return {"summary": summary, "clauses": all_clauses}


async def answer_question_about_document(doc_text: str, question: str) -> str:
    """Answer a user question grounded in document text using Groq (text-only)."""
    prompt = _chat_prompt(doc_text, question)
    try:
        return await _call_groq(prompt, max_tokens=1000)
    except Exception as exc:
        raise RuntimeError(f"Groq AI failed to answer: {exc}") from exc
