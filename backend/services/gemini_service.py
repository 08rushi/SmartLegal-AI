"""
Groq AI service — handles all AI operations:
- Legal document clause extraction + risk scoring (with page numbers)
- Multi-chunk processing for large documents
- Plain language rewriting in multiple languages
- Q&A on uploaded documents
"""

import json
import re
import asyncio
from openai import AsyncOpenAI
from config import get_settings

settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.gemini_api_key,
    base_url="https://api.groq.com/openai/v1",
)

MODEL = "llama-3.3-70b-versatile"
# Reduced chunk size: 10000 chars ~ 2500 tokens, leaves plenty of room for prompt + output
MAX_CHARS_PER_CHUNK = 10000


def _infer_document_type(document_text: str, filename: str = "") -> str:
    text = f"{filename}\n{document_text}".lower()
    if "leave and license" in text or "rent agreement" in text or "landlord" in text or "tenant" in text:
        return "Rental Agreement"
    if "employment" in text or "employer" in text or "employee" in text:
        return "Employment Contract"
    if "loan" in text or "lender" in text or "borrower" in text:
        return "Loan Agreement"
    if "service agreement" in text or "client" in text or "consultant" in text:
        return "Service Contract"
    return "Legal Document"


def _extract_parties_from_text(document_text: str) -> list[str]:
    parties: list[str] = []
    patterns = [
        r"Mr\.\s+[A-Z][A-Za-z\s]+",
        r"Ms\.\s+[A-Z][A-Za-z\s]+",
        r"Mrs\.\s+[A-Z][A-Za-z\s]+",
        r"M/s\.\s+[A-Z][A-Za-z0-9\s&.,-]+",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, document_text):
            cleaned = " ".join(match.split())
            if cleaned not in parties:
                parties.append(cleaned)
    return parties[:4]


def _extract_key_dates_from_text(document_text: str) -> list[dict]:
    matches = re.findall(
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+\s+\d{4})\b",
        document_text,
    )
    cleaned = []
    for item in matches:
        if item not in cleaned:
            cleaned.append(item)
    if not cleaned:
        return [
            {"label": "Start Date", "date": "N/A"},
            {"label": "End Date", "date": "N/A"},
        ]
    if len(cleaned) == 1:
        return [
            {"label": "Start Date", "date": cleaned[0]},
            {"label": "End Date", "date": "N/A"},
        ]
    return [
        {"label": "Start Date", "date": cleaned[0]},
        {"label": "End Date", "date": cleaned[1]},
    ]


def _clean_clause_title(raw_title: str, original_text: str) -> str:
    title = raw_title.strip(" -:\t")
    if title:
        return title[:80]
    snippet = re.sub(r"\s+", " ", original_text).strip()
    return snippet[:60] if snippet else "Clause"


def _classify_clause_risk(title: str, original_text: str) -> tuple[str, int, str, bool, str]:
    text = f"{title} {original_text}".lower()
    high_keywords = [
        "penalty",
        "forfeit",
        "evict",
        "unilateral",
        "indemn",
        "without notice",
        "terminate immediately",
    ]
    medium_keywords = [
        "notice",
        "termination",
        "jurisdiction",
        "repair",
        "damages",
        "deposit",
        "renewal",
        "sublet",
        "consent",
    ]
    beneficial_keywords = [
        "refundable",
        "landlord responsibility",
        "responsibility of the landlord",
        "mutual consent",
        "either party may terminate",
        "structural repairs shall be the responsibility of the landlord",
    ]

    risk_level = "low"
    risk_score = 3
    risk_reason = "This clause looks standard and relatively clear from the document text."

    if any(keyword in text for keyword in high_keywords):
        risk_level = "high"
        risk_score = 8
        risk_reason = "This clause may create a strong one-sided obligation or serious financial/legal downside."
    elif any(keyword in text for keyword in medium_keywords):
        risk_level = "medium"
        risk_score = 5
        risk_reason = "This clause should be reviewed carefully because it affects rights, obligations, or exit terms."

    beneficial = any(keyword in text for keyword in beneficial_keywords)
    beneficial_reason = ""
    if beneficial:
        beneficial_reason = "This clause gives some protection or balance to the user."

    return risk_level, risk_score, risk_reason, beneficial, beneficial_reason


def _extract_clauses_locally(document_text: str) -> list[dict]:
    clauses: list[dict] = []
    current_page = 1
    current_number = ""
    current_title = ""
    current_lines: list[str] = []

    clause_start_re = re.compile(r"^(\d+)\.\s*([^:\n]+):\s*(.*)$")
    bare_clause_start_re = re.compile(r"^(\d+)\.\s+(.+)$")

    def flush_clause() -> None:
        nonlocal current_number, current_title, current_lines
        if not current_lines:
            return
        original_text = " ".join(line.strip() for line in current_lines if line.strip())
        title = _clean_clause_title(current_title, original_text)
        risk_level, risk_score, risk_reason, beneficial, beneficial_reason = _classify_clause_risk(
            title,
            original_text,
        )
        clauses.append(
            {
                "id": f"local_{len(clauses) + 1}",
                "title": title,
                "clause_number": f"Clause {current_number}" if current_number else "Unnumbered",
                "page_number": current_page,
                "original_text": original_text,
                "plain_english": original_text,
                "plain_hindi": original_text,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_reason": risk_reason,
                "clause_type": title,
                "beneficial_to_user": beneficial,
                "beneficial_reason": beneficial_reason,
            }
        )
        current_number = ""
        current_title = ""
        current_lines = []

    for raw_line in document_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        page_match = re.match(r"^\[Page (\d+)\]$", line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        clause_match = clause_start_re.match(line)
        if clause_match:
            flush_clause()
            current_number = clause_match.group(1)
            current_title = clause_match.group(2)
            remainder = clause_match.group(3).strip()
            current_lines = [f"{current_title}: {remainder}" if remainder else current_title]
            continue

        bare_match = bare_clause_start_re.match(line)
        if bare_match and current_lines:
            flush_clause()
            current_number = bare_match.group(1)
            current_title = bare_match.group(2)[:60]
            current_lines = [bare_match.group(2).strip()]
            continue

        if current_lines:
            current_lines.append(line)

    flush_clause()
    return clauses


# ─── Chunk Analysis Prompt ───────────────────────────────────────────────────

CHUNK_PROMPT = """You are a senior Indian legal expert. Analyze this section of a legal document (chunk {chunk_index} of {total_chunks}, pages {start_page}-{end_page}).

DOCUMENT SECTION:
{document_text}

Return ONLY a valid JSON object (no markdown fences, no explanation). Structure:
{{"document_type":"Rental Agreement/Employment Contract/etc (chunk 1 only, else empty)","parties":["Party1","Party2"],"clauses":[{{"id":"c{chunk_index}_1","title":"Short name","clause_number":"Clause 5 or Section 3.2 (exact from doc)","page_number":{start_page},"original_text":"exact text","plain_english":"Simple 2-3 sentence explanation using you/your","plain_hindi":"Hindi mein 2-3 sentences","risk_level":"low","risk_score":3,"risk_reason":"Why risky with specific amounts/days","clause_type":"Rent/Termination/Penalty/etc","beneficial_to_user":false,"beneficial_reason":""}}]}}

Rules:
- Extract EVERY clause. Do not skip any.
- For clauses BENEFICIAL to user (tenant/employee/borrower), set beneficial_to_user=true and explain in beneficial_reason
- risk_level must be low/medium/high
- Include exact page numbers
- If clause number not in document, write "Unnumbered"
- Return valid JSON only"""


SUMMARY_PROMPT = """You are a senior Indian legal expert. Summarize this legal document analysis.

Document type: {document_type}
Parties: {parties}
Total pages: {total_pages}
Clauses found: {clause_count}

KEY CLAUSES SUMMARY:
{all_clauses_json}

Return ONLY valid JSON (no markdown):
{{"overall_risk":"medium","risk_summary":"3-4 sentences about main risks with specific clause/page refs","key_dates":[{{"label":"Start Date","date":"DD/MM/YYYY or N/A"}},{{"label":"End Date","date":"DD/MM/YYYY or N/A"}}],"high_risk_clauses":["Clause title (page X)"],"beneficial_clauses":["Clauses that protect/benefit the user"],"your_obligations":["Things you MUST do as tenant/employee/borrower"],"other_party_rights":["Key rights of landlord/employer/lender"]}}"""


# ─── Main Analysis Function ───────────────────────────────────────────────────

async def analyze_legal_document(document_text: str, filename: str) -> dict:
    """
    Analyze entire legal document using multi-chunk processing.
    Each chunk is analyzed separately, then results are merged.
    """
    from services.pdf_parser import split_into_chunks

    # Split document into smaller chunks
    chunks = split_into_chunks(document_text, max_chars=MAX_CHARS_PER_CHUNK)
    total_chunks = len(chunks)
    total_pages = max((c['end_page'] for c in chunks), default=1)

    print(f"[analyze] Processing {total_chunks} chunks, {total_pages} pages")

    # Analyze each chunk with delay between calls to avoid rate limits
    all_clauses = []
    document_type = _infer_document_type(document_text, filename)
    parties = _extract_parties_from_text(document_text)

    for i, chunk in enumerate(chunks):
        # Rate limit delay: wait 3 seconds between chunks
        if i > 0:
            await asyncio.sleep(3)

        try:
            prompt = CHUNK_PROMPT.format(
                chunk_index=i + 1,
                total_chunks=total_chunks,
                start_page=chunk['start_page'],
                end_page=chunk['end_page'],
                document_text=chunk['text'],
            )

            print(f"[analyze] Sending chunk {i+1}/{total_chunks} ({len(chunk['text'])} chars)...")

            response = await client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000,
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            raw = raw.strip()

            print(f"[analyze] Chunk {i+1} raw response length: {len(raw)}")

            chunk_result = json.loads(raw)

            # Collect document type and parties from first chunk only
            if i == 0:
                document_type = chunk_result.get("document_type", "") or document_type or "Legal Document"
                parties = chunk_result.get("parties", []) or parties

            # Collect clauses
            clauses = chunk_result.get("clauses", [])
            print(f"[analyze] Chunk {i+1} extracted {len(clauses)} clauses")
            all_clauses.extend(clauses)

        except json.JSONDecodeError as e:
            print(f"[analyze] Chunk {i+1} JSON parse failed: {e}")
            print(f"[analyze] Raw was: {raw[:500] if 'raw' in dir() else 'N/A'}")
            continue
        except Exception as e:
            print(f"[analyze] Chunk {i+1} failed: {type(e).__name__}: {e}")
            continue

    print(f"[analyze] Total clauses extracted: {len(all_clauses)}")

    if not all_clauses:
        print("[analyze] AI returned no clauses, using local clause extraction fallback")
        all_clauses = _extract_clauses_locally(document_text)
        print(f"[analyze] Local fallback extracted {len(all_clauses)} clauses")

    # Generate overall summary
    await asyncio.sleep(2)  # Brief pause before summary call
    summary_data = await _generate_summary(
        all_clauses, document_type, parties, total_pages
    )

    # Count risk levels
    high_count   = sum(1 for c in all_clauses if c.get("risk_level") == "high")
    medium_count = sum(1 for c in all_clauses if c.get("risk_level") == "medium")
    low_count    = sum(1 for c in all_clauses if c.get("risk_level") == "low")

    return {
        "summary": {
            "document_type": document_type or "Legal Document",
            "parties": parties,
            "key_dates": summary_data.get("key_dates", []) or _extract_key_dates_from_text(document_text),
            "overall_risk": summary_data.get("overall_risk", "medium"),
            "risk_summary": summary_data.get("risk_summary", ""),
            "high_risk_clauses": summary_data.get("high_risk_clauses", []),
            "beneficial_clauses": summary_data.get("beneficial_clauses", []),
            "your_obligations": summary_data.get("your_obligations", []),
            "other_party_rights": summary_data.get("other_party_rights", []),
            # Legacy fields for backward compatibility
            "tenant_obligations": summary_data.get("your_obligations", []),
            "landlord_rights": summary_data.get("other_party_rights", []),
            "total_clauses": len(all_clauses),
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "total_pages": total_pages,
            "chunks_analyzed": total_chunks,
        },
        "clauses": all_clauses,
    }


async def _generate_summary(
    all_clauses: list,
    document_type: str,
    parties: list,
    total_pages: int,
) -> dict:
    """Generate overall summary from all analyzed clauses."""
    try:
        # Send only compact key fields to save tokens
        compact_clauses = [
            {
                "title": c.get("title", ""),
                "clause_number": c.get("clause_number", ""),
                "page_number": c.get("page_number", ""),
                "risk_level": c.get("risk_level", ""),
                "risk_reason": c.get("risk_reason", "")[:200],
                "beneficial_to_user": c.get("beneficial_to_user", False),
                "beneficial_reason": c.get("beneficial_reason", "")[:100],
            }
            for c in all_clauses
        ]

        clauses_json = json.dumps(compact_clauses, ensure_ascii=False)
        # Trim to stay within token limits
        if len(clauses_json) > 8000:
            clauses_json = clauses_json[:8000] + "...]"

        prompt = SUMMARY_PROMPT.format(
            all_clauses_json=clauses_json,
            document_type=document_type,
            parties=", ".join(parties),
            total_pages=total_pages,
            clause_count=len(all_clauses),
        )

        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    except Exception as e:
        print(f"[analyze] Summary generation failed: {e}")
        # Generate a fallback summary from the clauses we have
        high_clauses = [
            f"{c.get('title', 'Unknown')} (page {c.get('page_number', '?')})"
            for c in all_clauses if c.get("risk_level") == "high"
        ]
        beneficial = [
            f"{c.get('title', 'Unknown')}: {c.get('beneficial_reason', '')}"
            for c in all_clauses if c.get("beneficial_to_user")
        ]
        return {
            "overall_risk": "medium",
            "risk_summary": f"Analyzed {len(all_clauses)} clauses across {total_pages} pages. Found {len(high_clauses)} high-risk clauses. Please review each clause carefully before signing.",
            "key_dates": [],
            "high_risk_clauses": high_clauses[:5],
            "beneficial_clauses": beneficial[:5],
            "your_obligations": [],
            "other_party_rights": [],
        }


# ─── Q&A Chat ────────────────────────────────────────────────────────────────

QA_PROMPT = """You are a helpful Indian legal assistant. Answer the question using ONLY the document below.

Rules:
- Reference exact clause numbers and page numbers (e.g. "Clause 5, Page 3 says...")
- If not in document: say "This is not mentioned in the document. Please consult a lawyer."
- Write simply — a class 8 student should understand
- End with a 2-line Hindi summary (हिंदी सारांश:)

DOCUMENT:
{document_text}

QUESTION: {question}

Answer:"""


async def answer_question_about_document(document_text: str, question: str) -> str:
    """Answer a user question about a specific legal document."""
    # Use first 18000 chars to stay within token limits
    truncated = document_text[:18000]

    prompt = QA_PROMPT.format(
        document_text=truncated,
        question=question,
    )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )

    return response.choices[0].message.content.strip()
