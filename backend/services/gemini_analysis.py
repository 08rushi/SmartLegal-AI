"""
gemini_analysis.py — whole-document legal analysis with Gemini (1M-token context).

Why: Groq's free tier allows ~8K tokens/minute, so a 50-page document needs ~20 sequential
chunks and 20-35 minutes. Gemini 2.5 Flash can take ~25K-token sections, so the same document
is 1-3 calls (a minute or two) at roughly a rupee or few per document.

Safety design:
  * Never required. `try_gemini_analysis` returns None whenever Gemini is not configured, not
    usable (e.g. 401/403 "free tier unavailable / billing off"), or fails — the caller then
    falls back to the existing Groq pipeline. No exception escapes.
  * Same output shape as the Groq pipeline, so validation, storage and the UI are unchanged.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from services.chunking_service import (
    ChunkingService,
    DocumentChunk,
    estimate_tokens,
    execute_chunks_with_retry,
)
from services.gemini_service import (
    _build_fallback_summary,
    _chunk_prompt,
    _classify_prompt,
    _extract_json,
    _summary_prompt,
    detect_document_type,
    get_doc_mode,
    get_law_context,
    parse_classification,
)
from services.model_capabilities import get_capability

logger = logging.getLogger(__name__)
settings = get_settings()

_REST_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# In "auto" mode, short documents stay on the free Groq path; longer ones use Gemini.
AUTO_MIN_TOKENS = 6000
# Above this many tokens, use the compact output format even on Gemini (keeps output bounded).
COMPACT_ABOVE_TOKENS = 150_000
CHUNK_TOKENS = 25_000

_unavailable_until: float = 0.0


class GeminiUnavailable(RuntimeError):
    """401/403 from Gemini: bad key, billing disabled, or free tier not available for the project."""


def text_model() -> str:
    return (getattr(settings, "gemini_text_model", "") or "").strip() or "gemini-2.5-flash"


def is_usable() -> bool:
    """True when a Gemini key is configured and we have not recently been refused access."""
    if not (getattr(settings, "gemini_api_key", "") or "").strip():
        return False
    return time.monotonic() >= _unavailable_until


def _mark_unavailable(seconds: float = 1800.0) -> None:
    global _unavailable_until
    _unavailable_until = time.monotonic() + seconds


def reset_availability() -> None:
    """Forget a previous refusal (used by tests / after the key or billing is fixed)."""
    global _unavailable_until
    _unavailable_until = 0.0


def _generation_config(model: str, max_out: int) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "temperature": 0.1,
        "maxOutputTokens": max_out,
        "responseMimeType": "application/json",
    }
    # 2.5 Flash/Flash-Lite "think" by default, which costs output tokens and time. Extraction
    # doesn't need it, so turn thinking off.
    if "2.5-flash" in model:
        cfg["thinkingConfig"] = {"thinkingBudget": 0}
    return cfg


async def _call_json(prompt: str, max_out: int = 32000) -> str:
    """One Gemini call returning the model's JSON text. Raises GeminiUnavailable on 401/403."""
    model = text_model()
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": _generation_config(model, max_out),
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=15.0)) as client:
        resp = await client.post(
            _REST_URL.format(model=model),
            headers={"x-goog-api-key": settings.gemini_api_key.strip()},
            json=payload,
        )

    code = resp.status_code
    if code in (401, 403):
        _mark_unavailable()
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        raise GeminiUnavailable(f"Gemini refused access (HTTP {code}): {detail}")
    if code == 429:
        raise RuntimeError(f"Gemini rate limit 429 on model '{model}'")
    if code >= 500:
        raise RuntimeError(f"Gemini temporary error {code} (connection/service unavailable)")
    if code != 200:
        raise RuntimeError(f"Gemini HTTP {code}: {resp.text[:200]}")

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates (response blocked or empty)")
    cand = candidates[0]
    if cand.get("finishReason") == "MAX_TOKENS":
        logger.warning("[gemini-analysis] output hit maxOutputTokens; JSON may be truncated (repair will be attempted)")
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
    if not text:
        raise RuntimeError("Gemini returned empty text")
    return text


async def _analyze(text: str, filename: str) -> Dict[str, Any]:
    from services.groq_service import _normalize_clause_payload  # shared wrapper-shape normaliser

    doc_type, doc_type_name = detect_document_type(text, filename)
    law_context = get_law_context(doc_type)
    mode = get_doc_mode(doc_type)

    # Preferred: LLM classification (falls back to keyword detection on any problem).
    try:
        classified = parse_classification(await _call_json(_classify_prompt(text, filename), max_out=800))
        if classified:
            doc_type_name, mode, law_from_llm = classified
            if law_from_llm:
                law_context = law_from_llm
    except GeminiUnavailable:
        raise
    except Exception as exc:
        logger.info("[gemini-analysis] classification failed, using keyword detection: %s", exc)

    total_tokens = estimate_tokens(text)
    compact = total_tokens > COMPACT_ABOVE_TOKENS
    cap = get_capability(text_model())
    chunker = ChunkingService(max_chunk_tokens=CHUNK_TOKENS, safety_margin=2000, capability=cap)
    chunks = chunker.chunk_text(text)
    if not chunks:
        raise RuntimeError("Gemini analysis: no text chunks available")
    print(f"[gemini-analysis] {total_tokens} tokens -> {len(chunks)} section(s) with {text_model()} (compact={compact})")

    async def _process(chunk: DocumentChunk) -> List[Dict[str, Any]]:
        prompt = _chunk_prompt(doc_type_name, law_context, chunk.text, chunk.chunk_index, mode, compact=compact)
        raw = await _call_json(prompt, max_out=32000)
        clauses = _normalize_clause_payload(_extract_json(raw))
        for c in clauses:
            c.setdefault("page_number", chunk.page_start)
            c.setdefault("chunk_index", chunk.chunk_index)
            if c.get("risk_level") not in ("low", "medium", "high"):
                c["risk_level"] = "medium"
            try:
                c["risk_score"] = max(1, min(10, int(c.get("risk_score", 5))))
            except (ValueError, TypeError):
                c["risk_score"] = 5
        return clauses

    all_clauses, meta = await execute_chunks_with_retry(
        chunks=chunks, chunk_processor=_process, max_retries=3, base_backoff_seconds=2.0
    )

    digest = [
        {
            "id": c.get("id"),
            "title": c.get("title"),
            "risk_level": c.get("risk_level"),
            "risk_reason": (c.get("risk_reason") or "")[:140],
        }
        for c in all_clauses[:40]
    ]
    try:
        summary = _extract_json(
            await _call_json(_summary_prompt(doc_type_name, law_context, json.dumps(digest, indent=1), mode), max_out=4000)
        )
        if not isinstance(summary, dict):
            raise ValueError("summary is not an object")
    except GeminiUnavailable:
        raise
    except Exception as exc:
        logger.info("[gemini-analysis] summary failed, using fallback summary: %s", exc)
        summary = _build_fallback_summary(doc_type_name, all_clauses)

    summary["total_clauses"] = len(all_clauses)
    summary["high_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "high")
    summary["medium_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
    summary["low_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "low")
    summary["is_partial"] = meta.get("is_partial", False)

    return {
        "summary": summary,
        "clauses": all_clauses,
        "metadata": {
            "completion_ratio": meta.get("completion_ratio", 1.0),
            "incomplete_chunks": meta.get("incomplete_chunks", []),
            "total_chunks": meta.get("total_chunks", len(chunks)),
            "successful_chunks": meta.get("successful_chunks", len(chunks)),
            "compact_mode": compact,
            "analysis_engine": "gemini",
            "analysis_model": text_model(),
        },
    }


async def try_gemini_analysis(text: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    Analyse with Gemini when appropriate; return None to tell the caller to use Groq.
    Never raises.
    """
    provider = (getattr(settings, "analysis_provider", "auto") or "auto").strip().lower()
    if provider == "groq" or not is_usable():
        return None
    if provider == "auto" and estimate_tokens(text) <= AUTO_MIN_TOKENS:
        return None  # short documents: free Groq path is fast enough
    try:
        return await _analyze(text, filename)
    except GeminiUnavailable as exc:
        print(f"[gemini-analysis] unavailable, using Groq instead: {exc}")
        return None
    except Exception as exc:
        print(f"[gemini-analysis] failed, using Groq instead: {exc}")
        return None
