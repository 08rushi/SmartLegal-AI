"""
Groq AI service for PDF text analysis.

Provider: Groq — the only LLM provider used at runtime. The model is read from
settings.groq_model (env GROQ_MODEL, default "openai/gpt-oss-120b").
Text-only: No image support.
"""

import json
import asyncio
import time
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


# ── Gemini REST fallback (text-only) ─────────────────────────────────────────
# Models tried in order when the primary Groq provider is unavailable.
# These are real, supported model IDs on the generativelanguage v1beta API.
_GEMINI_TEXT_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-2.5-pro",
]

_gemini_permanently_unavailable: bool = False


class GeminiPermanentError(RuntimeError):
    """Raised when Gemini returns a non-retryable error (401, 403, 404)."""


class GeminiRateLimitError(RuntimeError):
    """Raised when Gemini returns 429 — caller should back off and retry."""


async def _call_gemini_rest(model: str, prompt: str, max_tokens: int, api_key: str) -> str:
    """Single attempt against one Gemini model via the REST API.

    Raises:
        GeminiPermanentError: for 401, 403, 404 — skip this model, don't retry.
        GeminiRateLimitError: for 429 — caller should wait and retry.
        RuntimeError: for other HTTP errors or empty responses.
    """
    global _gemini_permanently_unavailable
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": min(max_tokens, 8192)},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
        response = await client.post(url, headers={"x-goog-api-key": api_key}, json=payload)

    code = response.status_code
    if code in (401, 403, 404):
        # Parse a safe error message — never include the api_key in the log
        try:
            detail = response.json().get("error", {}).get("message", response.text[:200])
        except Exception:
            detail = response.text[:200]
        if code in (401, 403):
            # Project-level access denial or invalid key affects all models under this project
            _gemini_permanently_unavailable = True
        raise GeminiPermanentError(
            f"Gemini model '{model}' permanently unavailable (HTTP {code}): {detail}"
        )
    if code == 429:
        raise GeminiRateLimitError(f"Gemini model '{model}' rate-limited (HTTP 429).")
    if code != 200:
        raise RuntimeError(f"Gemini model '{model}' failed (HTTP {code}): {response.text[:200]}")

    data = response.json()
    candidates = data.get("candidates") or []
    parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
    content = "".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
    if not content:
        raise RuntimeError(f"Gemini model '{model}' returned no text content.")
    return content


async def _fallback_to_gemini(prompt: str, max_tokens: int = 4000) -> str:
    """Try Gemini text models in order as a provider fallback.

    Model selection order:
      1. GEMINI_TEXT_MODEL (if set)
      2. GEMINI_VISION_MODEL (if set and not disabled)
      3. _GEMINI_TEXT_FALLBACK_MODELS list

    Skips models that return permanent errors (401/403/404).
    Raises RuntimeError if all models fail.
    """
    global _gemini_permanently_unavailable
    if _gemini_permanently_unavailable:
        raise GeminiPermanentError("Gemini fallback skipped: Google project permanently denied access or unauthorized.")

    api_key = getattr(settings, "gemini_api_key", "")
    if not api_key:
        raise RuntimeError("Gemini fallback is not configured (GEMINI_API_KEY is empty).")

    # Build ordered model list: configured text/vision model first (if set), then fallbacks
    models_to_try = []
    text_model = getattr(settings, "gemini_text_model", "").strip()
    if text_model and text_model not in models_to_try:
        models_to_try.append(text_model)
    vision_model = getattr(settings, "gemini_vision_model", "").strip()
    if vision_model and vision_model not in models_to_try:
        models_to_try.append(vision_model)
    for m in _GEMINI_TEXT_FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error: Exception = RuntimeError("No Gemini models configured.")
    for model in models_to_try:
        try:
            print(f"[gemini-fallback] Trying model '{model}'...")
            result = await _call_gemini_rest(model, prompt, max_tokens, api_key)
            print(f"[gemini-fallback] Success with model '{model}'.")
            return result
        except GeminiPermanentError as exc:
            print(f"[gemini-fallback] Model '{model}' permanently unavailable — skipping. ({exc})")
            last_error = exc
            if _gemini_permanently_unavailable:
                # Stop immediately if project-level authorization failed
                break
            continue  # try next model
        except GeminiRateLimitError as exc:
            print(f"[gemini-fallback] Model '{model}' rate-limited — skipping remaining models.")
            last_error = exc
            break  # rate-limited: no point trying more models immediately
        except Exception as exc:
            print(f"[gemini-fallback] Model '{model}' failed: {exc}")
            last_error = exc
            continue

    raise RuntimeError(f"All Gemini fallback models failed. Last error: {last_error}")


# ── Reuse Gemini Service Helpers ──────────────────────────────────────────────

from services.gemini_service import (
    DOCUMENT_TEMPLATES,
    detect_document_type,
    get_law_context,
    get_doc_mode,
    _classify_prompt,
    parse_classification,
    _extract_json,
    _build_fallback_summary,
    _chunk_prompt,
    _summary_prompt,
    _chat_prompt,
)


# ── Groq API Calls ───────────────────────────────────────────────────────────

def _reasoning_kwargs(effort: str) -> dict:
    """gpt-oss models 'think' before answering and that thinking eats max_tokens (default effort
    truncated JSON mid-way). Ask for less reasoning; other models ignore this."""
    if "gpt-oss" in (settings.groq_model or ""):
        return {"extra_body": {"reasoning_effort": effort}}
    return {}


def _estimate_request_tokens(text: str, max_tokens: int) -> int:
    """Realistic token cost of one call: prompt + the output we actually expect (not the max_tokens cap)."""
    from services.chunking_service import estimate_tokens
    prompt_tokens = estimate_tokens(text)
    # Measured on real runs: output ≈ 0.6-0.9x the prompt for clause extraction, so don't
    # reserve the full max_tokens (that made the pacer ~2x too conservative).
    expected_out = max(800, min(max_tokens, 3500, int(prompt_tokens * 0.9)))
    est = prompt_tokens + expected_out
    limit = int(getattr(settings, "groq_tpm_limit", 8000) or 8000)
    return max(1, min(est, limit - 100))  # a single call must always be able to fit the window


async def _wait_for_groq_slot(request_tokens: int, cap, max_wait: float = 75.0) -> bool:
    """
    Free-tier Groq allows only ~8K tokens/minute. When the window is full, WAIT for it to
    clear (≤ max_wait seconds) instead of failing the chunk. Long limits (e.g. the daily cap,
    retry-after of many minutes) return False immediately so callers can fall back / report.
    """
    from services.provider_budget_manager import budget_manager

    waited = 0.0
    while True:
        if await budget_manager.can_send(request_tokens, cap):
            return True
        status = budget_manager.get_provider_status("groq") if hasattr(budget_manager, "get_provider_status") else {}
        wait = status.get("retry_after_remaining", 0.0) or 0.0
        if wait <= 0:
            hdr = getattr(budget_manager, "_header_states", {}).get("groq", {})
            wait = hdr.get("reset_tokens") or hdr.get("reset_requests") or 5.0
        if wait > max_wait - waited:
            return False  # long cooldown (daily limit etc.) — don't sit here
        wait = max(1.0, min(float(wait), 30.0)) + 0.5
        print(f"[groq] Rate-limit window full — waiting {wait:.0f}s for capacity...")
        await asyncio.sleep(wait)
        waited += wait


async def _call_groq(prompt: str, max_tokens: int = 4000) -> str:
    """Call Groq API with token accounting and automatic OpenRouter fallback."""
    from services.model_capabilities import get_capability
    from services.provider_budget_manager import budget_manager, parse_rate_limit_headers
    from services.openrouter_service import is_openrouter_configured, call_openrouter

    cap = get_capability(settings.groq_model)
    can_send_groq = await _wait_for_groq_slot(_estimate_request_tokens(prompt, max_tokens), cap)
    if not can_send_groq:
        if is_openrouter_configured():
            try:
                print(f"[groq] Groq budget/cooldown blocked ({max_tokens} tokens). Falling back to OpenRouter.")
                return await call_openrouter(prompt, max_tokens=max_tokens)
            except Exception as fallback_exc:
                print(f"[groq] OpenRouter fallback failed: {fallback_exc}")
        if getattr(settings, "gemini_api_key", "") and not _gemini_permanently_unavailable:
            try:
                print("[groq] Groq unavailable; falling back to Gemini text generation.")
                return await _fallback_to_gemini(prompt, max_tokens=max_tokens)
            except Exception as fb_exc:
                print(f"[groq] Gemini fallback failed: {fb_exc}")
        status = budget_manager.get_provider_status("groq") if hasattr(budget_manager, "get_provider_status") else {}
        cooloff = status.get("retry_after_remaining", 0.0) or 0.0
        if cooloff <= 0:
            header_info = getattr(budget_manager, "_header_states", {}).get("groq", {})
            reset_tok = header_info.get("reset_tokens")
            if reset_tok:
                rec_at = header_info.get("recorded_at", time.monotonic())
                cooloff = max(1.0, (rec_at + reset_tok) - time.monotonic())
            else:
                cooloff = 5.0
        raise RuntimeError(f"Groq is currently rate-limited or in cooloff ({cooloff:.1f}s remaining); primary AI provider is temporarily unavailable.")

    loop = asyncio.get_event_loop()

    def _sync_call():
        client = _get_groq_client()
        try:
            raw_res = client.chat.completions.with_raw_response.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
                **_reasoning_kwargs("low"),
            )
            completion = raw_res.parse()
            headers = dict(raw_res.headers)
            tokens = getattr(getattr(completion, "usage", None), "total_tokens", max_tokens)
            content = completion.choices[0].message.content or ""
            return content, tokens, headers
        except AttributeError:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
                **_reasoning_kwargs("low"),
            )
            tokens = getattr(getattr(completion, "usage", None), "total_tokens", max_tokens)
            content = completion.choices[0].message.content or ""
            return content, tokens, {}

    try:
        content, tokens_used, headers = await loop.run_in_executor(None, _sync_call)
        await budget_manager.record_success("groq", settings.groq_model, tokens_used, headers=headers)
        return content
    except Exception as exc:
        resp = getattr(exc, "response", None)
        headers = dict(getattr(resp, "headers", {})) if resp else {}
        is_429 = getattr(exc, "status_code", None) == 429 or "429" in str(exc) or "rate limit" in str(exc).lower()
        if is_429:
            parsed = parse_rate_limit_headers(headers)
            retry_after = parsed.get("retry_after") or 60.0
            await budget_manager.record_rate_limit("groq", int(round(retry_after)), headers=headers)

        if is_openrouter_configured():
            try:
                print(f"[groq] Groq call failed ({exc}). Executing OpenRouter fallback...")
                return await call_openrouter(prompt, max_tokens=max_tokens)
            except Exception as fallback_exc:
                print(f"[groq] OpenRouter fallback failed: {fallback_exc}")
        if getattr(settings, "gemini_api_key", "") and not _gemini_permanently_unavailable:
            try:
                print(f"[groq] Groq call failed ({exc}); trying Gemini fallback...")
                return await _fallback_to_gemini(prompt, max_tokens=max_tokens)
            except Exception as fb_exc:
                print(f"[groq] Gemini fallback failed: {fb_exc}")
        raise exc


async def _call_groq_chat(messages: list[dict], max_tokens: int = 1800, temperature: float = 0.2) -> str:
    """Call Groq chat with token accounting and automatic OpenRouter fallback."""
    from services.model_capabilities import get_capability
    from services.provider_budget_manager import budget_manager, parse_rate_limit_headers
    from services.openrouter_service import is_openrouter_configured, call_openrouter_chat

    cap = get_capability(settings.groq_model)
    chat_text = " ".join(str(m.get("content", "")) for m in messages)
    can_send_groq = await _wait_for_groq_slot(_estimate_request_tokens(chat_text, max_tokens), cap)
    if not can_send_groq:
        if is_openrouter_configured():
            try:
                print(f"[groq] Groq budget/cooldown blocked ({max_tokens} tokens). Falling back to OpenRouter chat.")
                return await call_openrouter_chat(messages, max_tokens=max_tokens, temperature=temperature)
            except Exception as fallback_exc:
                print(f"[groq] OpenRouter chat fallback failed: {fallback_exc}")
        if getattr(settings, "gemini_api_key", ""):
            prompt = "\n\n".join(f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages)
            print("[groq] Groq unavailable; falling back to Gemini chat generation.")
            return await _fallback_to_gemini(prompt, max_tokens=max_tokens)
        status = budget_manager.get_provider_status("groq") if hasattr(budget_manager, "get_provider_status") else {}
        cooloff = status.get("retry_after_remaining", 60.0) or 60.0
        raise RuntimeError(f"Groq is currently rate-limited or in cooloff ({cooloff:.1f}s remaining); configure Gemini or OpenRouter fallback to continue.")

    loop = asyncio.get_event_loop()

    def _sync_call():
        client = _get_groq_client()
        try:
            raw_res = client.chat.completions.with_raw_response.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **_reasoning_kwargs("medium"),
            )
            completion = raw_res.parse()
            headers = dict(raw_res.headers)
            tokens = getattr(getattr(completion, "usage", None), "total_tokens", max_tokens)
            content = completion.choices[0].message.content or ""
            return content, tokens, headers
        except AttributeError:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **_reasoning_kwargs("medium"),
            )
            tokens = getattr(getattr(completion, "usage", None), "total_tokens", max_tokens)
            content = completion.choices[0].message.content or ""
            return content, tokens, {}

    try:
        content, tokens_used, headers = await loop.run_in_executor(None, _sync_call)
        await budget_manager.record_success("groq", settings.groq_model, tokens_used, headers=headers)
        return content
    except Exception as exc:
        resp = getattr(exc, "response", None)
        headers = dict(getattr(resp, "headers", {})) if resp else {}
        is_429 = getattr(exc, "status_code", None) == 429 or "429" in str(exc) or "rate limit" in str(exc).lower()
        if is_429:
            parsed = parse_rate_limit_headers(headers)
            retry_after = parsed.get("retry_after") or 60.0
            await budget_manager.record_rate_limit("groq", int(round(retry_after)), headers=headers)

        if is_openrouter_configured():
            try:
                print(f"[groq] Groq chat call failed ({exc}). Executing OpenRouter fallback...")
                return await call_openrouter_chat(messages, max_tokens=max_tokens, temperature=temperature)
            except Exception as fallback_exc:
                print(f"[groq] OpenRouter chat fallback failed: {fallback_exc}")
        if getattr(settings, "gemini_api_key", ""):
            prompt = "\n\n".join(f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages)
            return await _fallback_to_gemini(prompt, max_tokens=max_tokens)
        raise exc


# ── Virtual Legal Advisor (general Indian-law consultation, no document) ───────

LEGAL_ADVISOR_SYSTEM_PROMPT = """You are "SmartLegal AI Advisor" — a highly experienced Indian advocate and legal consultant with deep practice across civil, criminal, family, consumer, property, labour, corporate and constitutional law. A citizen is consulting you about a real legal problem. Advise them like a seasoned, practical lawyer.

WHAT YOU HELP WITH:
- Contracts & documents the user is about to enter into: which clauses are essential, which protective terms to insert, which terms to be careful of or negotiate/remove, plus stamp duty, registration, jurisdiction and dispute-resolution needs.
- Disputes & court cases: identify the correct forum and the exact cause of action; the applicable Constitution of India Articles and the relevant Acts and sections; the strengths and weaknesses of the case; an honest, realistic (never guaranteed) assessment of the chances of success with reasons; the evidence required; the limitation period; and a practical strategy including cheaper/faster alternatives (legal notice, mediation, Lok Adalat, settlement).
- General rights, procedure and "what should I do next" questions.

HOW TO ANSWER:
1. If key facts are missing, briefly ask 1-3 focused clarifying questions first — but still give useful preliminary guidance based on reasonable assumptions (state the assumptions).
2. Give a clear, structured answer using short headings or bullets. A typical answer covers: your position / applicable law, the strong and weak points, and concrete recommended steps.
3. Cite the EXACT provisions: Constitution Articles (e.g. Article 21, 226, 32), and statute sections. For criminal matters prefer the 2023 codes — Bharatiya Nyaya Sanhita 2023 (BNS), Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS), Bharatiya Sakshya Adhiniyam 2023 (BSA) — and note the erstwhile IPC/CrPC section in brackets. Use the right family/consumer/property/labour statutes as applicable (Hindu Marriage Act 1955, Special Marriage Act 1954, Negotiable Instruments Act 1881 s.138, Consumer Protection Act 2019, Transfer of Property Act 1882, Specific Relief Act 1963, CPC 1908, Limitation Act 1963, etc.).
4. Give ACTIONABLE, specific suggestions — e.g. "instead of relying on X, your stronger ground is section Y because…", "add an arbitration + exclusive-jurisdiction clause", "send a legal notice first under…". When the user asks which Articles/sections to add to strengthen a case, recommend the most relevant ones and explain why, and warn against weak/irrelevant ones.
5. Be honest about uncertainty and risk. Chances of success depend on facts, evidence and forum — never promise an outcome.

FORMATTING:
- Use clean Markdown: **bold** for key terms, and bullet or numbered lists for steps.
- Use a Markdown table only for genuinely tabular content (e.g. steps → what happens → outcome, or option-by-option comparison). Keep tables to 2-3 columns with short cells so they render well on mobile. Always include the header separator row (e.g. | --- | --- |) and keep every row's pipe count identical.

RULES:
- Ground everything in Indian law. NEVER invent Article numbers, section numbers, or case names. If unsure of a precise section, name only the Act and say the exact provision should be confirmed.
- Be practical and specific, not vague. Prefer real, current Indian law.
- Reply in the user's language. If they write in or ask for Hindi, answer in Hindi.
- Always end with exactly this line: "Note: This is AI legal guidance based on Indian law, not a substitute for a licensed advocate. Outcomes depend on your specific facts, evidence and forum — please consult a qualified lawyer before acting."
"""


async def get_legal_advice(message: str, history: list[dict] | None = None) -> str:
    """General Indian-law consultation (no uploaded document required)."""
    messages: list[dict] = [{"role": "system", "content": LEGAL_ADVISOR_SYSTEM_PROMPT}]
    for m in (history or [])[-12:]:
        role = "assistant" if m.get("role") == "assistant" else "user"
        content = str(m.get("content", "")).strip()
        if content:
            messages.append({"role": role, "content": content[:2500]})
    messages.append({"role": "user", "content": message.strip()})
    try:
        return await _call_groq_chat(messages, max_tokens=1900, temperature=0.25)
    except Exception as exc:
        raise RuntimeError(f"Advisor failed to answer: {exc}") from exc


# ── Public API ────────────────────────────────────────────────────────────────

def _normalize_clause_payload(parsed: object) -> list[dict]:
    """Normalize common model response wrappers to the canonical clause list."""
    if isinstance(parsed, list):
        clauses = parsed
    elif isinstance(parsed, dict):
        clauses = None
        for key in (
            "clauses", "items", "results", "extracted_clauses", "analysis",
            "data", "sections", "provisions", "content", "points"
        ):
            value = parsed.get(key)
            if isinstance(value, list):
                clauses = value
                break
            if isinstance(value, dict):
                nested = value.get("clauses") or value.get("items") or value.get("results")
                if isinstance(nested, list):
                    clauses = nested
                    break
        if clauses is None:
            # Check if any top-level key contains a list of items/dicts
            for val in parsed.values():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], (dict, str)):
                    clauses = val
                    break
        if clauses is None and any(k in parsed for k in ("original_text", "clause_text", "title", "clause_title")):
            clauses = [parsed]
        if clauses is None:
            raise ValueError(
                "AI returned a JSON object without a clause array. "
                f"Available keys: {', '.join(map(str, parsed.keys()))[:200]}"
            )
    else:
        raise ValueError(f"AI clause response must be an array or wrapped object, got {type(parsed).__name__}")

    normalized = []
    for item in clauses:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, str) and item.strip():
            normalized.append({"title": "Extracted legal point", "original_text": item.strip()})
    if not normalized:
        raise ValueError("AI returned no usable clauses for this document section.")
    return normalized

async def analyze_legal_document(text: str, filename: str) -> dict:
    """
    Analyze a legal document text using Groq (text-only, PDFs only).

    Args:
        text: Extracted PDF text with page markers
        filename: Original filename for type detection

    Returns:
        {summary, clauses} with same schema
    """
    # Long documents: prefer Gemini's 1M-token context (1-3 calls instead of ~20 rate-limited
    # Groq chunks). Returns None when Gemini isn't configured/usable/fails → Groq path below.
    from services.gemini_analysis import try_gemini_analysis
    gemini_result = await try_gemini_analysis(text, filename)
    if gemini_result is not None:
        return gemini_result

    doc_type, doc_type_name = detect_document_type(text, filename)
    law_context = get_law_context(doc_type)
    mode = get_doc_mode(doc_type)

    print(f"[groq] Keyword detection: {doc_type} ({doc_type_name}) for '{filename}'")

    # ── LLM classification (preferred over keyword scoring) ──
    try:
        raw_cls = await _call_groq(_classify_prompt(text, filename), max_tokens=400)
        classified = parse_classification(raw_cls)
        if classified:
            doc_type_name, mode, law_from_llm = classified
            if law_from_llm:
                law_context = law_from_llm
            print(f"[groq] LLM classified as: {doc_type_name} (mode={mode})")
    except Exception as exc:
        print(f"[groq] Classification step failed, using keyword detection: {exc}")

    from services.chunking_service import (
        ChunkingService,
        DocumentChunk,
        execute_chunks_with_retry,
    )
    from services.model_capabilities import get_capability
    from services.provider_budget_manager import budget_manager

    # Sized safely based on configured ModelCapability and safety margins
    cap = get_capability(settings.groq_model)
    from services.chunking_service import estimate_tokens
    # Long documents switch to compact output + bigger chunks (fewer calls, less prompt overhead,
    # ~40-60% fewer tokens in total) so free-tier limits can still finish them.
    compact = estimate_tokens(text) > 6000   # ≈ more than 5-6 dense pages
    chunker = ChunkingService(
        max_chunk_tokens=2000,   # dense clauses emit ~1.4x as many output tokens as input — keep chunks small
        safety_margin=1200,
        capability=cap,
    )
    chunks = chunker.chunk_text(text)
    print(f"[groq] Split text into {len(chunks)} token-bounded chunks (compact_mode={compact})")

    if not chunks:
        raise RuntimeError("Groq analysis failed: no text chunks were available.")

    async def _process_chunk_fn(chunk: DocumentChunk) -> list[dict]:
        prompt = _chunk_prompt(doc_type_name, law_context, chunk.text, chunk.chunk_index, mode, compact=compact)
        # Check remaining budget to choose safe max_tokens between 3000 and 6000
        header_info = getattr(budget_manager, "_header_states", {}).get("groq", {})
        rem_tok = header_info.get("remaining_tokens")
        if compact:
            target_max_tokens = 4500
        elif rem_tok is not None and rem_tok >= 2500 and rem_tok < 6000:
            target_max_tokens = min(4000, rem_tok)
        else:
            target_max_tokens = 6000
        raw = await _call_groq(prompt, max_tokens=target_max_tokens)
        parsed = _normalize_clause_payload(_extract_json(raw))

        for clause in parsed:
            clause.setdefault("page_number", chunk.page_start)
            clause.setdefault("chunk_index", chunk.chunk_index)
            if clause.get("risk_level") not in ("low", "medium", "high"):
                clause["risk_level"] = "medium"
            try:
                score = int(clause.get("risk_score", 5))
                clause["risk_score"] = max(1, min(10, score))
            except (ValueError, TypeError):
                clause["risk_score"] = 5

        print(f"[groq] Chunk {chunk.chunk_id} done: {len(parsed)} clauses extracted")
        return parsed

    # Execute with bounded retries and partial-failure preservation
    all_clauses, chunk_meta = await execute_chunks_with_retry(
        chunks=chunks,
        chunk_processor=_process_chunk_fn,
        max_retries=3,
        base_backoff_seconds=1.0,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    compact_clauses = [
        {
            "id": c.get("id"),
            "title": c.get("title"),
            "risk_level": c.get("risk_level"),
            "risk_reason": c.get("risk_reason", "")[:120],
        }
        for c in all_clauses[:20]
    ]
    summary_prompt = _summary_prompt(
        doc_type_name, law_context, json.dumps(compact_clauses, indent=2), mode
    )
    try:
        raw_summary = await _call_groq(summary_prompt, max_tokens=2500)
        summary = _extract_json(raw_summary)
        summary["total_clauses"] = len(all_clauses)
        summary["high_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "high")
        summary["medium_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
        summary["low_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "low")
        summary["is_partial"] = chunk_meta.get("is_partial", False)
    except Exception as exc:
        print(f"[groq] Summary failed: {exc}")
        summary = _build_fallback_summary(doc_type_name, all_clauses)
        summary["is_partial"] = chunk_meta.get("is_partial", False)

    return {
        "summary": summary,
        "clauses": all_clauses,
        "metadata": {
            "completion_ratio": chunk_meta.get("completion_ratio", 1.0),
            "incomplete_chunks": chunk_meta.get("incomplete_chunks", []),
            "total_chunks": chunk_meta.get("total_chunks", len(chunks)),
            "successful_chunks": chunk_meta.get("successful_chunks", len(chunks)),
            "compact_mode": compact,
        },
    }


async def answer_question_about_document(
    doc_text: str,
    question: str,
    doc_type_name: str | None = None,
    law_context: str | None = None,
    analysis_summary: dict | None = None,
    history: list | None = None,
) -> str:
    """Answer a user question grounded in document text + Indian law using Groq."""
    prompt = _chat_prompt(doc_text, question, doc_type_name, law_context, analysis_summary, history)
    try:
        return await _call_groq(prompt, max_tokens=1600)
    except Exception as exc:
        raise RuntimeError(f"Groq AI failed to answer: {exc}") from exc


# ── Insight generators (consequences + negotiation) ───────────────────────────

_LEVELS = ("low", "medium", "high")


def _clauses_digest(clauses: list, limit: int = 30) -> str:
    """Compact clause list for insight prompts — keeps the useful fields, trims text."""
    rows = []
    for c in clauses[:limit]:
        rows.append({
            "id": c.get("id"),
            "title": c.get("title"),
            "clause_type": c.get("clause_type"),
            "risk_level": c.get("risk_level"),
            "original_text": (c.get("original_text") or "")[:600],
            "risk_reason": (c.get("risk_reason") or "")[:400],
        })
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _norm_level(value, default: str = "medium") -> str:
    return value if value in _LEVELS else default


def _consequences_prompt(doc_type_name: str, summary: dict, clauses: list) -> str:
    return f"""You are an experienced Indian advocate. The user is about to SIGN a "{doc_type_name}".
Simulate — in concrete, realistic terms — what could actually happen TO THE USER if they sign this document AS-IS and things go wrong later. Base it strictly on the clauses provided; do not invent terms that are not present.

DOCUMENT SUMMARY:
{json.dumps(summary, ensure_ascii=False)[:2500]}

CLAUSES:
{_clauses_digest(clauses)}

Return ONLY valid JSON (no markdown, no prose outside JSON) in EXACTLY this shape:
{{
  "overview": "2-3 sentence plain-English summary of the user's real-world exposure if they sign as-is",
  "overall_exposure": "low|medium|high",
  "scenarios": [
    {{
      "id": "s1",
      "category": "Financial|Legal Rights|Obligations|Exit / Termination|Liability|Privacy / Data",
      "title": "short scenario name",
      "trigger": "the situation/event that would set this off",
      "outcome": "exactly what happens to the user (rights lost, money owed, penalties)",
      "worst_case": "concrete worst case, with rupee amounts or duration when the clause implies them",
      "severity": "low|medium|high",
      "likelihood": "low|medium|high",
      "plain_english": "friendly one-line explanation",
      "plain_hindi": "same explanation in simple Hindi",
      "related_clause": "the clause title this comes from, or empty string"
    }}
  ]
}}
Rules: 4-8 scenarios, most severe first. Cite Indian law in the outcome where relevant (e.g. Transfer of Property Act, Consumer Protection Act 2019, Indian Contract Act 1872). Never promise certainty. Output JSON only."""


def _negotiation_prompt(doc_type_name: str, summary: dict, clauses: list) -> str:
    return f"""You are an experienced Indian advocate helping the user NEGOTIATE a "{doc_type_name}" before signing.
For the clauses that are unfair, one-sided, or risky for the user, give a safer alternative and copy-ready replacement wording they can actually send to the other party. Base everything strictly on the clauses provided.

DOCUMENT SUMMARY:
{json.dumps(summary, ensure_ascii=False)[:2000]}

CLAUSES:
{_clauses_digest(clauses)}

Return ONLY valid JSON (no markdown, no prose outside JSON) in EXACTLY this shape:
{{
  "summary": "2-3 sentence read on the user's overall leverage and the top things to push back on",
  "items": [
    {{
      "id": "n1",
      "clause_title": "the clause being renegotiated",
      "risk_level": "low|medium|high",
      "current_problem": "why the current wording hurts the user",
      "suggested_change": "plain-English description of the fairer version to ask for",
      "counter_text": "copy-ready replacement clause text the user can paste/send",
      "talking_point": "one practical sentence to say when negotiating this",
      "plain_hindi": "the suggested_change explained in simple Hindi"
    }}
  ]
}}
Rules: cover the 4-8 most important clauses to renegotiate, highest-risk first. Keep counter_text professional and legally sensible under Indian law. Output JSON only."""


async def simulate_consequences(doc_type_name: str, summary: dict, clauses: list) -> dict:
    """'What happens if I sign?' — realistic consequence simulation from a stored analysis."""
    raw = await _call_groq(_consequences_prompt(doc_type_name or "legal document", summary or {}, clauses or []), max_tokens=3200)
    data = _extract_json(raw)
    if not isinstance(data, dict):
        raise RuntimeError("Consequence simulation returned an unexpected shape.")
    data["overall_exposure"] = _norm_level(data.get("overall_exposure"))
    scenarios = data.get("scenarios") if isinstance(data.get("scenarios"), list) else []
    for i, s in enumerate(scenarios):
        s["id"] = s.get("id") or f"s{i + 1}"
        s["severity"] = _norm_level(s.get("severity"))
        s["likelihood"] = _norm_level(s.get("likelihood"))
    data["scenarios"] = scenarios
    return data


async def generate_negotiation(doc_type_name: str, summary: dict, clauses: list) -> dict:
    """Negotiation helper — safer-clause alternatives + copy-ready counter text."""
    raw = await _call_groq(_negotiation_prompt(doc_type_name or "legal document", summary or {}, clauses or []), max_tokens=3600)
    data = _extract_json(raw)
    if not isinstance(data, dict):
        raise RuntimeError("Negotiation helper returned an unexpected shape.")
    items = data.get("items") if isinstance(data.get("items"), list) else []
    for i, it in enumerate(items):
        it["id"] = it.get("id") or f"n{i + 1}"
        it["risk_level"] = _norm_level(it.get("risk_level"))
    data["items"] = items
    return data

