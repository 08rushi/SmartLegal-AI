"""
Groq AI service for PDF text analysis.

Provider: Groq — the only LLM provider used at runtime. The model is read from
settings.groq_model (env GROQ_MODEL, default "openai/gpt-oss-120b").
Text-only: No image support.
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

async def _call_groq(prompt: str, max_tokens: int = 4000) -> str:
    """Call Groq API synchronously (wrapped in async)."""
    loop = asyncio.get_event_loop()

    def _sync_call():
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    return await loop.run_in_executor(None, _sync_call)


async def _call_groq_chat(messages: list[dict], max_tokens: int = 1800, temperature: float = 0.2) -> str:
    """Call Groq with a full messages array (system + conversation)."""
    loop = asyncio.get_event_loop()

    def _sync_call():
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    return await loop.run_in_executor(None, _sync_call)


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

    from services.pdf_parser import split_into_chunks

    # max_chars is sized so a single chunk request stays safely under Groq's
    # on-demand-tier 8000 TPM limit even for token-dense scripts (Devanagari/
    # Tamil/Bengali OCR text tokenizes far less efficiently than English —
    # measured ~2.5 chars/token worst case vs ~4 for English). At 12000 chars
    # a dense non-English chunk alone could request >10000 tokens, which the
    # API rejects outright (413) — that request can never succeed, retry or
    # not. max_tokens is scaled down by the same ratio so the output budget
    # per input char is unchanged from before.
    chunks = split_into_chunks(text, max_chars=6000)
    print(f"[groq] Split text into {len(chunks)} chunks")

    all_clauses = []
    chunk_errors = []

    if not chunks:
        raise RuntimeError("Groq analysis failed: no text chunks were available.")

    # Serialized (not parallel) so multiple chunks can't stack past the
    # account's shared per-minute token budget within the same window.
    sem = asyncio.Semaphore(1)

    async def _process_chunk(i: int, chunk: dict) -> list:
        async with sem:
            prompt = _chunk_prompt(doc_type_name, law_context, chunk["text"], i, mode)
            try:
                raw = await _call_groq(prompt, max_tokens=2500)
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
                    print(f"[groq] Chunk {i + 1} done: {len(parsed)} clauses extracted")
                    return parsed
                else:
                    msg = f"Chunk {i + 1}: unexpected response shape {type(parsed).__name__}"
                    chunk_errors.append(msg)
                    print(f"[groq] {msg}, skipping")
            except Exception as exc:
                msg = f"Chunk {i + 1} failed: {exc}"
                chunk_errors.append(msg)
                print(f"[groq] {msg}")
            return []

    chunk_results = await asyncio.gather(*[_process_chunk(i, chunk) for i, chunk in enumerate(chunks)])
    for res in chunk_results:
        all_clauses.extend(res)


    if not all_clauses:
        detail = "; ".join(chunk_errors[:3]) if chunk_errors else "the model returned no clauses"
        raise RuntimeError(
            "We couldn't extract any clauses from this document. It may be a scanned "
            "image, use a non-Unicode font, or not be a legal document. Please try a "
            f"text-based PDF where the text can be selected. (detail: {detail})"
        )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary_prompt = _summary_prompt(
        doc_type_name, law_context, json.dumps(all_clauses[:20], indent=2), mode
    )
    try:
        raw_summary = await _call_groq(summary_prompt, max_tokens=2600)
        summary = _extract_json(raw_summary)
        summary["total_clauses"] = len(all_clauses)
        summary["high_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "high")
        summary["medium_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
        summary["low_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "low")
    except Exception as exc:
        print(f"[groq] Summary failed: {exc}")
        summary = _build_fallback_summary(doc_type_name, all_clauses)

    return {"summary": summary, "clauses": all_clauses}


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
