"""
Gemini AI service — handles all AI operations:
- Legal document clause extraction + risk scoring
- Plain English + Hindi rewriting
- Q&A on uploaded documents
"""

import json
import re
from openai import AsyncOpenAI
from config import get_settings

settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.gemini_api_key,
    base_url="https://api.groq.com/openai/v1",
)


# ─── Document Analysis ───────────────────────────────────────────────────────

ANALYSIS_PROMPT = """
You are a senior Indian legal expert and a plain-language writer. 
Analyze the following legal document and return a structured JSON response.

DOCUMENT TEXT:
{document_text}

FILENAME: {filename}

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "summary": {{
    "document_type": "e.g. Rental Agreement / Employment Contract / Loan Agreement",
    "parties": ["Party 1 name", "Party 2 name"],
    "key_dates": [
      {{"label": "Start Date", "date": "DD/MM/YYYY or N/A"}},
      {{"label": "End Date", "date": "DD/MM/YYYY or N/A"}}
    ],
    "overall_risk": "low|medium|high",
    "risk_summary": "2-3 sentences summarizing the main risks in plain language",
    "total_clauses": 0,
    "high_risk_count": 0,
    "medium_risk_count": 0,
    "low_risk_count": 0
  }},
  "clauses": [
    {{
      "id": "clause_1",
      "title": "Short clause name",
      "original_text": "The exact original clause text",
      "plain_english": "Rewrite in simple English. Max 2-3 sentences. Use 'you' to address the reader.",
      "plain_hindi": "Hindi mein simple explanation. Max 2-3 sentences.",
      "risk_level": "low|medium|high",
      "risk_score": 5,
      "risk_reason": "Why is this risky? Be specific. E.g. 'The landlord can evict you with only 7 days notice, but you need 60 days.'",
      "clause_type": "e.g. Rent, Termination, Security Deposit, Notice Period, Liability, Penalty"
    }}
  ]
}}

Rules:
- Extract ALL important clauses (at least 5-10)
- risk_score is 1-10 (1=safe, 10=very risky)
- For high risk clauses: explain EXACTLY why it's one-sided or harmful
- plain_english must be understood by a class 10 student
- plain_hindi must be in Devanagari script
- Focus on India-specific issues: security deposit limits, notice periods, arbitration clauses
- Flag one-sided clauses (e.g. landlord can terminate with 7 days but tenant needs 60 days)
"""


async def analyze_legal_document(document_text: str, filename: str) -> dict:
    """
    Send document to Gemini and get structured clause analysis.
    """
    # Truncate to ~30k chars to stay within context limits
    truncated = document_text[:30000]

    prompt = ANALYSIS_PROMPT.format(
        document_text=truncated,
        filename=filename,
    )

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=8192,
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    result = json.loads(raw)

    # Ensure clause IDs are set
    for i, clause in enumerate(result.get("clauses", [])):
        if not clause.get("id"):
            clause["id"] = f"clause_{i + 1}"

    # Update counts in summary
    clauses = result.get("clauses", [])
    summary = result.get("summary", {})
    summary["total_clauses"] = len(clauses)
    summary["high_risk_count"] = sum(1 for c in clauses if c.get("risk_level") == "high")
    summary["medium_risk_count"] = sum(1 for c in clauses if c.get("risk_level") == "medium")
    summary["low_risk_count"] = sum(1 for c in clauses if c.get("risk_level") == "low")

    return result


# ─── Q&A Chat ────────────────────────────────────────────────────────────────

QA_PROMPT = """
You are a helpful legal assistant for Indian users.
You have been given a legal document. Answer the user's question using ONLY the information in the document.

If the document does not contain information to answer the question, say:
"This specific matter is not clearly mentioned in the document. I recommend consulting a lawyer."

Be direct and clear. Write in simple English.
If helpful, also provide a brief Hindi explanation after your English answer.

DOCUMENT:
{document_text}

USER QUESTION: {question}

Answer:"""


async def answer_question_about_document(document_text: str, question: str) -> str:
    """
    Answer a user question about a specific legal document.
    Uses RAG-style prompting — the document IS the context.
    """
    truncated = document_text[:25000]

    prompt = QA_PROMPT.format(
        document_text=truncated,
        question=question,
    )

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
