"""
AI analysis service using Google Gemini.

Provider: Google Gemini (gemini-2.0-flash)
Multimodal: Supports text (PDFs) and images (JPEG, PNG, WebP) natively.
Fallback: Groq handles PDFs only via text extraction.
"""

import json
import base64
import re
import asyncio
from typing import Union

import google.generativeai as genai
from config import get_settings

settings = get_settings()


# ── Gemini Client Setup ───────────────────────────────────────────────────────

# Models tried in order when a daily quota is exhausted on the previous one.
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def _make_gemini_model(model_name: str) -> genai.GenerativeModel:
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=8192,
        ),
    )


# ── Document Type Detection ───────────────────────────────────────────────────

DOCUMENT_TEMPLATES = {
    "rental_agreement": {
        "name": "Rental Agreement",
        "keywords": ["rent", "tenant", "landlord", "lease", "premises", "deposit", "eviction", "maintenance"],
    },
    "employment_contract": {
        "name": "Employment Contract",
        "keywords": ["employee", "employer", "salary", "probation", "termination", "notice period", "designation"],
    },
    "loan_agreement": {
        "name": "Loan Agreement",
        "keywords": ["loan", "borrower", "lender", "interest", "repayment", "collateral", "emi", "default"],
    },
    "property_sale": {
        "name": "Property Sale Agreement",
        "keywords": ["sale", "buyer", "seller", "property", "possession", "registration", "stamp duty"],
    },
    "service_contract": {
        "name": "Service Contract",
        "keywords": ["service", "client", "vendor", "deliverable", "milestone", "payment terms", "liability"],
    },
    "nda": {
        "name": "Non-Disclosure Agreement",
        "keywords": ["confidential", "nda", "disclosure", "proprietary", "trade secret", "non-disclosure"],
    },
    "partnership_deed": {
        "name": "Partnership Deed",
        "keywords": ["partner", "partnership", "profit", "loss", "capital", "dissolution", "firm"],
    },
    "fir_criminal": {
        "name": "FIR Criminal",
        "keywords": ["fir", "first information report", "police", "ipc", "complaint", "accused", "investigation"],
    },
    "court_notice": {
        "name": "Court Notice",
        "keywords": ["court", "notice", "summon", "plaintiff", "defendant", "hearing", "judgment", "decree"],
    },
    "divorce_petition": {
        "name": "Divorce Petition",
        "keywords": ["divorce", "petition", "matrimonial", "spouse", "custody", "alimony", "maintenance"],
    },
    "consumer_complaint": {
        "name": "Consumer Complaint",
        "keywords": ["consumer", "complaint", "deficiency", "service", "goods", "forum", "compensation"],
    },
    "insurance_policy": {
        "name": "Insurance Policy",
        "keywords": ["insurance", "policy", "premium", "claim", "insured", "beneficiary", "coverage"],
    },
    "franchise_agreement": {
        "name": "Franchise Agreement",
        "keywords": ["franchise", "franchisee", "franchisor", "royalty", "territory", "rights"],
    },
    "will_testament": {
        "name": "Will / Testament",
        "keywords": ["will", "testament", "heir", "estate", "executor", "beneficiary", "legacy"],
    },
    "vehicle_transfer": {
        "name": "Vehicle Transfer",
        "keywords": ["vehicle", "car", "transfer", "ownership", "registration", "insurance"],
    },
    "general": {
        "name": "Legal Document",
        "keywords": [],
    },
}


def detect_document_type(text: str, filename: str) -> tuple[str, str]:
    """Detect document type by keyword scoring."""
    sample = (filename + " " + text[:3000]).lower()
    scores = {}
    for doc_type, info in DOCUMENT_TEMPLATES.items():
        if doc_type == "general":
            continue
        scores[doc_type] = sum(1 for kw in info["keywords"] if kw in sample)
    best = max(scores, key=scores.get) if scores else "general"
    if scores.get(best, 0) == 0:
        best = "general"
    return best, DOCUMENT_TEMPLATES[best]["name"]


# ── Indian Law KB ─────────────────────────────────────────────────────────────

def get_law_context(doc_type: str) -> str:
    """Get Indian law context for document type."""
    contexts = {
        "rental_agreement": "Relevant laws: Transfer of Property Act 1882, Rent Control Acts (state-specific), Indian Contract Act 1872.",
        "employment_contract": "Relevant laws: Industrial Disputes Act 1947, Shops and Establishments Act (state-specific), Payment of Gratuity Act 1972, Minimum Wages Act 1948.",
        "loan_agreement": "Relevant laws: Indian Contract Act 1872, SARFAESI Act 2002, RBI guidelines on lending.",
        "property_sale": "Relevant laws: Transfer of Property Act 1882, Registration Act 1908, Indian Stamp Act 1899.",
        "consumer_complaint": "Relevant laws: Consumer Protection Act 2019.",
        "fir_criminal": "Relevant laws: Code of Criminal Procedure 1973, Indian Penal Code 1860, BNSS 2023.",
        "court_notice": "Relevant laws: Code of Civil Procedure 1908, Limitation Act 1963.",
    }
    return contexts.get(doc_type, "Relevant laws: Indian Contract Act 1872.")


# ── JSON Extraction Helper ────────────────────────────────────────────────────

def _extract_json(text: str) -> Union[dict, list]:
    """Strip markdown fences and parse JSON from model output."""
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        match = re.search(pattern, cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    raise ValueError(f"No valid JSON found in response: {cleaned[:200]}")


# ── Prompts ───────────────────────────────────────────────────────────────────

def _chunk_prompt(doc_type_name: str, law_context: str, chunk_text: str, chunk_index: int) -> str:
    return f"""You are a senior Indian lawyer reviewing a {doc_type_name}.
{law_context}

Extract EVERY clause from this document section (chunk {chunk_index + 1}).
Return ONLY a valid JSON array. No explanation, no markdown, no preamble.

Each clause object must have exactly these fields:
{{
  "id": "clause_<number>",
  "title": "Short clause title",
  "original_text": "Exact text from document",
  "plain_english": "Simple English explanation (2-3 sentences)",
  "plain_hindi": "Simple Hindi explanation (2-3 sentences)",
  "risk_level": "low" | "medium" | "high",
  "risk_score": <1-10>,
  "risk_reason": "Why this is risky, citing specific Indian law if applicable",
  "clause_type": "e.g. Rent, Termination, Deposit, Notice Period",
  "beneficial_to_user": true | false
}}

Document section:
{chunk_text}

Return ONLY the JSON array:"""


def _summary_prompt(doc_type_name: str, law_context: str, clauses_json: str) -> str:
    return f"""You are a senior Indian lawyer. Based on the extracted clauses below, write a summary for this {doc_type_name}.
{law_context}

Return ONLY a valid JSON object. No explanation, no markdown.

Required fields:
{{
  "document_type": "{doc_type_name}",
  "parties": ["Party 1 name", "Party 2 name"],
  "key_dates": [{{"label": "Start Date", "date": "DD/MM/YYYY"}}],
  "overall_risk": "low" | "medium" | "high",
  "risk_summary": "2-3 sentence plain English summary of overall risk",
  "high_risk_clauses": ["Brief description of each high risk clause"],
  "beneficial_clauses": ["Brief description of clauses that protect the user"],
  "your_obligations": ["Key things the user must do"],
  "other_party_rights": ["Key rights the other party has"],
  "total_clauses": <number>,
  "high_risk_count": <number>,
  "medium_risk_count": <number>,
  "low_risk_count": <number>
}}

Extracted clauses:
{clauses_json}

Return ONLY the JSON object:"""


def _chat_prompt(doc_text: str, question: str) -> str:
    return f"""You are a helpful Indian legal assistant. Answer the user's question based ONLY on the document provided.
- Cite specific clauses where possible
- Reference relevant Indian laws where applicable
- Use simple, clear language
- Keep answer between 150-250 words
- End with: "Note: This is AI-assisted analysis, not formal legal advice. Consult a qualified lawyer for legal decisions."

Document:
{doc_text[:8000]}

Question: {question}

Answer:"""


def _image_analysis_prompt(doc_type_name: str, law_context: str) -> str:
    """Combined clause extraction + summary for images (single-pass analysis)."""
    return f"""You are a senior Indian lawyer analyzing a legal document image ({doc_type_name}).
{law_context}

Extract ALL clauses from this document image and provide a summary.
Return ONLY valid JSON with this exact structure:

{{
  "summary": {{
    "document_type": "{doc_type_name}",
    "parties": ["party names"],
    "key_dates": [{{"label": "Date type", "date": "DD/MM/YYYY"}}],
    "overall_risk": "low" | "medium" | "high",
    "risk_summary": "2-3 sentence plain English summary of overall risk",
    "high_risk_clauses": ["clause descriptions"],
    "beneficial_clauses": ["clause descriptions"],
    "your_obligations": ["your obligations"],
    "other_party_rights": ["other party rights"],
    "total_clauses": <number>,
    "high_risk_count": <number>,
    "medium_risk_count": <number>,
    "low_risk_count": <number>
  }},
  "clauses": [
    {{
      "id": "clause_1",
      "title": "clause title",
      "original_text": "exact text from document",
      "plain_english": "2-3 sentence simple explanation",
      "plain_hindi": "2-3 sentence simple Hindi explanation",
      "risk_level": "low" | "medium" | "high",
      "risk_score": <1-10>,
      "risk_reason": "Why risky, citing Indian law section",
      "clause_type": "Clause category",
      "beneficial_to_user": true | false
    }}
  ]
}}

Return ONLY the JSON object:"""


# ── Fallback Summary Builder ──────────────────────────────────────────────────

def _build_fallback_summary(doc_type_name: str, clauses: list) -> dict:
    high = sum(1 for c in clauses if c.get("risk_level") == "high")
    med = sum(1 for c in clauses if c.get("risk_level") == "medium")
    low = sum(1 for c in clauses if c.get("risk_level") == "low")
    return {
        "document_type": doc_type_name,
        "parties": [],
        "key_dates": [],
        "overall_risk": "medium",
        "risk_summary": (
            "AI analysis encountered an issue extracting clauses. "
            "Please try re-analyzing the document. "
            "If the problem persists, ensure the PDF contains selectable text, not scanned images."
        ),
        "high_risk_clauses": [],
        "beneficial_clauses": [],
        "your_obligations": [],
        "other_party_rights": [],
        "total_clauses": len(clauses),
        "high_risk_count": high,
        "medium_risk_count": med,
        "low_risk_count": low,
    }


# ── Async Gemini Wrappers ─────────────────────────────────────────────────────

def _is_daily_quota(exc_str: str) -> bool:
    """True when the 429 is a per-day quota violation (retrying won't help today)."""
    return "PerDay" in exc_str or "per_day" in exc_str.lower()


def _retry_delay_seconds(exc_str: str) -> int:
    """Parse the retry_delay.seconds hint from a Gemini 429 message."""
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", exc_str)
    return int(m.group(1)) + 2 if m else 30


async def _call_gemini(prompt: str, image_data: bytes = None, mime_type: str = None) -> str:
    """
    Call Gemini API with model fallback and per-minute retry.

    Strategy:
      - Try each model in GEMINI_MODEL_FALLBACKS in order.
      - On a per-minute 429: wait the API-suggested delay and retry the same model once.
      - On a per-day 429: skip to the next model (each model has its own daily quota).
      - On any other error: re-raise immediately.
    """
    loop = asyncio.get_event_loop()
    last_exc: Exception | None = None

    for model_name in GEMINI_MODEL_FALLBACKS:
        model = _make_gemini_model(model_name)

        def _sync_call(_model=model):
            if image_data and mime_type:
                response = _model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": image_data},
                ])
            else:
                response = _model.generate_content(prompt)
            return response.text or ""

        for attempt in range(2):  # 0 = first try, 1 = one retry after waiting
            try:
                return await loop.run_in_executor(None, _sync_call)
            except Exception as exc:
                exc_str = str(exc)
                last_exc = exc

                if "429" not in exc_str:
                    raise  # not a quota error — surface immediately

                if _is_daily_quota(exc_str):
                    print(f"[gemini] Daily quota exhausted for {model_name}, trying next model")
                    break  # move to next model in fallback list

                if attempt == 0:
                    wait = _retry_delay_seconds(exc_str)
                    print(f"[gemini] Per-minute rate limit on {model_name}, waiting {wait}s then retrying")
                    await asyncio.sleep(wait)
                else:
                    print(f"[gemini] Still rate-limited after wait on {model_name}, trying next model")
                    break  # move to next model

    raise RuntimeError(
        f"All Gemini models exhausted their quota. "
        f"Last error: {last_exc}. "
        f"Options: (1) wait until quota resets, (2) enable billing at aistudio.google.com, "
        f"(3) create a new API key in a fresh project."
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze_legal_document(
    file_bytes_or_text: Union[bytes, str],
    filename: str,
    file_type: str = "pdf",
) -> dict:
    """
    Analyze a legal document (text from PDF or image bytes).

    Args:
        file_bytes_or_text: PDF text extracted (str) or image bytes (bytes)
        filename: Original filename
        file_type: 'pdf' or 'image' (jpeg/png/webp)

    Returns:
        {summary, clauses} with same schema as before
    """
    if isinstance(file_bytes_or_text, bytes) and file_type == "pdf":
        raise ValueError("For PDFs, pass extracted text, not bytes. Use pdf_parser.extract_text_from_pdf()")

    # Detect document type from filename/text
    if isinstance(file_bytes_or_text, str):
        # Text-based PDF
        doc_type, doc_type_name = detect_document_type(file_bytes_or_text, filename)
        text = file_bytes_or_text
        is_image = False
    else:
        # Image file
        doc_type, doc_type_name = detect_document_type("", filename)
        text = ""
        is_image = True

    law_context = get_law_context(doc_type)

    print(f"[gemini] Detected document type: {doc_type} ({doc_type_name}) for '{filename}'")

    # ── Image Analysis (single-pass) ──
    if is_image:
        print(f"[gemini] Analyzing image with Gemini Vision API...")
        prompt = _image_analysis_prompt(doc_type_name, law_context)
        try:
            raw = await _call_gemini(prompt, image_data=file_bytes_or_text, mime_type="image/jpeg")
            result = _extract_json(raw)

            # Ensure clauses are properly formatted
            if isinstance(result, dict):
                clauses = result.get("clauses", [])
                summary = result.get("summary", {})
            else:
                # Unexpected format
                clauses = []
                summary = _build_fallback_summary(doc_type_name, clauses)

            # Normalize risk levels
            for clause in clauses:
                if clause.get("risk_level") not in ("low", "medium", "high"):
                    clause["risk_level"] = "medium"
                try:
                    score = int(clause.get("risk_score", 5))
                    clause["risk_score"] = max(1, min(10, score))
                except (ValueError, TypeError):
                    clause["risk_score"] = 5

            if not clauses:
                raise ValueError("Gemini returned no clauses for the uploaded image.")

            print(f"[gemini] Image analysis done: {len(clauses)} clauses extracted")
            return {"summary": summary, "clauses": clauses}

        except Exception as exc:
            print(f"[gemini] Image analysis failed: {exc}")
            raise RuntimeError(f"Gemini image analysis failed: {exc}") from exc

    # ── Text-Based PDF Analysis (chunked) ──
    from services.pdf_parser import split_into_chunks

    chunks = split_into_chunks(text, max_chars=12000)
    print(f"[gemini] Split text into {len(chunks)} chunks")

    all_clauses = []
    chunk_errors = []

    if not chunks:
        raise RuntimeError("Gemini analysis failed: no text chunks were available.")

    for i, chunk in enumerate(chunks):
        prompt = _chunk_prompt(doc_type_name, law_context, chunk["text"], i)
        try:
            raw = await _call_gemini(prompt)
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
                print(f"[gemini] Chunk {i + 1} done: {len(parsed)} clauses extracted")
            else:
                msg = f"Chunk {i + 1}: unexpected response shape {type(parsed).__name__}"
                chunk_errors.append(msg)
                print(f"[gemini] {msg}, skipping")

        except Exception as exc:
            msg = f"Chunk {i + 1} failed: {exc}"
            chunk_errors.append(msg)
            print(f"[gemini] {msg}")

    if not all_clauses:
        reason = "; ".join(chunk_errors[:3]) if chunk_errors else "model returned empty clause arrays"
        raise RuntimeError(f"Gemini extracted zero clauses from readable text. {reason}")

    # ── Summary ───────────────────────────────────────────────────────────────
    summary_prompt = _summary_prompt(
        doc_type_name, law_context, json.dumps(all_clauses[:20], indent=2)
    )
    try:
        raw_summary = await _call_gemini(summary_prompt)
        summary = _extract_json(raw_summary)
        summary["total_clauses"] = len(all_clauses)
        summary["high_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "high")
        summary["medium_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
        summary["low_risk_count"] = sum(1 for c in all_clauses if c.get("risk_level") == "low")
    except Exception as exc:
        print(f"[gemini] Summary failed: {exc}")
        summary = _build_fallback_summary(doc_type_name, all_clauses)

    return {"summary": summary, "clauses": all_clauses}


async def answer_question_about_document(doc_text: str, question: str) -> str:
    """Answer a user question grounded in document text using Gemini."""
    prompt = _chat_prompt(doc_text, question)
    try:
        return await _call_gemini(prompt)
    except Exception as exc:
        raise RuntimeError(f"AI failed to answer: {exc}") from exc
