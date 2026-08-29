"""
AI analysis service using Google Gemini.

Provider: Optional Google Gemini legacy helper.
Live path: Groq handles PDF text extraction and analysis.
Note: image/OCR analysis is not part of the current production flow.
"""

import json
import base64
import re
import asyncio
from typing import Union

try:
    import google.generativeai as genai
except ImportError:
    genai = None
from config import get_settings
from services.prompt_registry import PROMPT_INJECTION_SAFETY_HEADER

settings = get_settings()


# ── Gemini Client Setup ───────────────────────────────────────────────────────

# Models tried in order when a daily quota is exhausted on the previous one.
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def _make_gemini_model(model_name: str):
    if genai is None:
        raise RuntimeError("google-generativeai is not installed. Install it to use Gemini analysis.")
    genai.configure(api_key=getattr(settings, "gemini_api_key", ""))
    return genai.GenerativeModel(
        model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=8192,
        ),
    )


# ── Document Type Detection ───────────────────────────────────────────────────

# Every template: name, mode ("agreement" = contract/deed review, "case" = court/
# litigation file), keywords (for the offline fallback classifier), and acts (the
# Indian statutes the LLM should ground its analysis in — cited by section).
DOCUMENT_TEMPLATES = {
    # ── Agreements / deeds / instruments ─────────────────────────────────────
    "rental_agreement": {
        "name": "Rental / Lease Agreement", "mode": "agreement",
        "keywords": ["rent", "tenant", "landlord", "lease", "premises", "deposit", "eviction", "licensee", "lock-in"],
        "acts": ["Transfer of Property Act 1882 (ss.105-108)", "the State Rent Control Act", "Registration Act 1908", "Indian Contract Act 1872"],
    },
    "employment_contract": {
        "name": "Employment Contract / Offer Letter", "mode": "agreement",
        "keywords": ["employee", "employer", "salary", "probation", "termination", "notice period", "designation", "ctc", "appointment"],
        "acts": ["Code on Wages 2019", "Industrial Relations Code 2020", "Payment of Gratuity Act 1972", "Employees' Provident Funds Act 1952", "Shops and Establishments Act (state)", "Indian Contract Act 1872 (s.27 restraint of trade)"],
    },
    "loan_agreement": {
        "name": "Loan Agreement", "mode": "agreement",
        "keywords": ["loan", "borrower", "lender", "interest", "repayment", "collateral", "emi", "default", "principal"],
        "acts": ["Indian Contract Act 1872", "SARFAESI Act 2002", "RBI Fair Practices Code", "Indian Stamp Act 1899"],
    },
    "promissory_note": {
        "name": "Promissory Note", "mode": "agreement",
        "keywords": ["promissory", "promise to pay", "on demand", "bearer", "payee", "maker"],
        "acts": ["Negotiable Instruments Act 1881", "Indian Stamp Act 1899"],
    },
    "property_sale": {
        "name": "Agreement to Sell (Property)", "mode": "agreement",
        "keywords": ["agreement to sell", "buyer", "seller", "possession", "advance", "sale consideration", "stamp duty"],
        "acts": ["Transfer of Property Act 1882", "Registration Act 1908", "Indian Stamp Act 1899", "Specific Relief Act 1963", "RERA 2016"],
    },
    "sale_deed": {
        "name": "Sale Deed / Conveyance Deed", "mode": "agreement",
        "keywords": ["sale deed", "conveyance", "vendor", "vendee", "hereby convey", "absolute owner", "sub-registrar"],
        "acts": ["Transfer of Property Act 1882 (s.54)", "Registration Act 1908 (s.17)", "Indian Stamp Act 1899"],
    },
    "gift_deed": {
        "name": "Gift Deed", "mode": "agreement",
        "keywords": ["gift", "donor", "donee", "natural love and affection", "without consideration", "settlement deed"],
        "acts": ["Transfer of Property Act 1882 (ss.122-129)", "Registration Act 1908", "Indian Stamp Act 1899"],
    },
    "mortgage_deed": {
        "name": "Mortgage Deed", "mode": "agreement",
        "keywords": ["mortgage", "mortgagor", "mortgagee", "charge", "redemption", "hypothecation"],
        "acts": ["Transfer of Property Act 1882 (ss.58-104)", "Registration Act 1908", "SARFAESI Act 2002"],
    },
    "power_of_attorney": {
        "name": "Power of Attorney", "mode": "agreement",
        "keywords": ["power of attorney", "attorney", "principal", "hereby appoint", "gpa", "attorney holder"],
        "acts": ["Powers of Attorney Act 1882", "Registration Act 1908", "Indian Stamp Act 1899"],
    },
    "service_contract": {
        "name": "Service / Vendor Contract", "mode": "agreement",
        "keywords": ["service", "client", "vendor", "deliverable", "milestone", "payment terms", "liability", "sow", "consultant"],
        "acts": ["Indian Contract Act 1872", "Information Technology Act 2000", "Consumer Protection Act 2019"],
    },
    "nda": {
        "name": "Non-Disclosure Agreement", "mode": "agreement",
        "keywords": ["confidential", "nda", "disclosure", "proprietary", "trade secret", "non-disclosure", "receiving party"],
        "acts": ["Indian Contract Act 1872", "Information Technology Act 2000"],
    },
    "partnership_deed": {
        "name": "Partnership Deed", "mode": "agreement",
        "keywords": ["partner", "partnership", "profit sharing", "capital", "dissolution", "firm", "profit and loss"],
        "acts": ["Indian Partnership Act 1932", "Indian Contract Act 1872"],
    },
    "llp_agreement": {
        "name": "LLP Agreement", "mode": "agreement",
        "keywords": ["llp", "limited liability partnership", "designated partner", "contribution", "dpin"],
        "acts": ["Limited Liability Partnership Act 2008"],
    },
    "mou": {
        "name": "Memorandum of Understanding", "mode": "agreement",
        "keywords": ["memorandum of understanding", "mou", "understanding", "intent", "non-binding", "parties intend"],
        "acts": ["Indian Contract Act 1872"],
    },
    "franchise_agreement": {
        "name": "Franchise Agreement", "mode": "agreement",
        "keywords": ["franchise", "franchisee", "franchisor", "royalty", "territory", "brand"],
        "acts": ["Indian Contract Act 1872", "Trade Marks Act 1999", "Competition Act 2002"],
    },
    "will_testament": {
        "name": "Will / Testament", "mode": "agreement",
        "keywords": ["will", "testament", "testator", "heir", "estate", "executor", "bequeath", "legacy"],
        "acts": ["Indian Succession Act 1925", "Hindu Succession Act 1956"],
    },
    "succession_certificate": {
        "name": "Succession / Legal Heir Document", "mode": "agreement",
        "keywords": ["succession certificate", "legal heir", "heirship", "deceased", "intestate"],
        "acts": ["Indian Succession Act 1925", "Hindu Succession Act 1956"],
    },
    "vehicle_transfer": {
        "name": "Vehicle Transfer / RC", "mode": "agreement",
        "keywords": ["vehicle", "rc", "chassis", "transfer of ownership", "registration certificate", "form 29", "form 30"],
        "acts": ["Motor Vehicles Act 1988", "Central Motor Vehicles Rules 1989"],
    },
    "insurance_policy": {
        "name": "Insurance Policy", "mode": "agreement",
        "keywords": ["insurance", "policy", "premium", "sum insured", "insured", "nominee", "coverage", "exclusion"],
        "acts": ["Insurance Act 1938", "IRDAI regulations", "Consumer Protection Act 2019"],
    },
    "indemnity_bond": {
        "name": "Indemnity Bond / Affidavit", "mode": "agreement",
        "keywords": ["indemnity", "bond", "affidavit", "deponent", "solemnly affirm", "surety"],
        "acts": ["Indian Contract Act 1872 (ss.124-125)", "Bharatiya Sakshya Adhiniyam 2023"],
    },
    "rent_receipt": {
        "name": "Rent Receipt / Acknowledgement", "mode": "agreement",
        "keywords": ["rent receipt", "received a sum", "acknowledgement", "towards rent"],
        "acts": ["Indian Contract Act 1872", "Income Tax Act 1961 (HRA)"],
    },

    # ── Court / litigation / case files ──────────────────────────────────────
    "fir_criminal": {
        "name": "FIR (First Information Report)", "mode": "case",
        "keywords": ["fir", "first information report", "police station", "u/s", "accused", "complainant", "cognizable"],
        "acts": ["Bharatiya Nyaya Sanhita 2023 (BNS, replaced IPC 1860)", "Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS s.173, replaced CrPC s.154)", "Bharatiya Sakshya Adhiniyam 2023"],
    },
    "theft_case": {
        "name": "Theft / Robbery Case File", "mode": "case",
        "keywords": ["theft", "stolen", "robbery", "burglary", "dacoity", "snatching", "misappropriation", "stealing"],
        "acts": ["BNS 2023 s.303 (theft; erstwhile IPC 378/379)", "BNS 2023 s.309 (robbery)", "BNS 2023 s.305 (theft in dwelling)", "BNSS 2023"],
    },
    "missing_person": {
        "name": "Missing Person Report", "mode": "case",
        "keywords": ["missing", "untraceable", "whereabouts", "last seen", "missing person", "gone missing"],
        "acts": ["BNSS 2023 (police duty to trace)", "BNS 2023 ss.137-140 (kidnapping/abduction, if suspected)", "Guidelines of the National Human Rights Commission on missing persons"],
    },
    "charge_sheet": {
        "name": "Charge Sheet (Police Report)", "mode": "case",
        "keywords": ["charge sheet", "chargesheet", "final report", "u/s 173", "investigation", "prosecution"],
        "acts": ["BNSS 2023 s.193 (police report; erstwhile CrPC s.173)", "Bharatiya Nyaya Sanhita 2023", "Bharatiya Sakshya Adhiniyam 2023"],
    },
    "bail_application": {
        "name": "Bail Application", "mode": "case",
        "keywords": ["bail", "anticipatory bail", "applicant", "surety", "bond", "custody", "enlarge on bail"],
        "acts": ["BNSS 2023 ss.478-483 (bail; erstwhile CrPC ss.437-439)", "Bharatiya Nyaya Sanhita 2023"],
    },
    "criminal_complaint": {
        "name": "Criminal Complaint", "mode": "case",
        "keywords": ["complaint", "complainant", "accused", "magistrate", "cognizance", "private complaint"],
        "acts": ["BNSS 2023 s.223 (complaint to Magistrate; erstwhile CrPC s.200)", "Bharatiya Nyaya Sanhita 2023"],
    },
    "civil_suit": {
        "name": "Civil Suit / Plaint", "mode": "case",
        "keywords": ["plaint", "plaintiff", "defendant", "suit", "cause of action", "prayer", "decree", "relief"],
        "acts": ["Code of Civil Procedure 1908", "Specific Relief Act 1963", "Limitation Act 1963", "Court Fees Act 1870"],
    },
    "written_statement": {
        "name": "Written Statement / Defence", "mode": "case",
        "keywords": ["written statement", "defendant", "denies", "para-wise", "set-off", "counter claim"],
        "acts": ["Code of Civil Procedure 1908 (Order VIII)", "Limitation Act 1963"],
    },
    "court_summons": {
        "name": "Court Summons / Notice", "mode": "case",
        "keywords": ["summons", "notice", "hereby summoned", "appear before", "hearing", "next date", "cause list"],
        "acts": ["Code of Civil Procedure 1908 (Order V)", "BNSS 2023 (criminal summons)", "Limitation Act 1963"],
    },
    "legal_notice": {
        "name": "Legal Notice", "mode": "case",
        "keywords": ["legal notice", "advocate", "on behalf of my client", "call upon", "failing which", "within 15 days"],
        "acts": ["Indian Contract Act 1872", "Negotiable Instruments Act 1881 s.138 (if cheque)", "Consumer Protection Act 2019"],
    },
    "judgment_order": {
        "name": "Judgment / Court Order", "mode": "case",
        "keywords": ["judgment", "order", "hon'ble", "coram", "in the matter of", "ordered", "disposed", "held"],
        "acts": ["Code of Civil Procedure 1908 / BNSS 2023", "Constitution of India", "the substantive Act in issue"],
    },
    "divorce_petition": {
        "name": "Divorce Petition", "mode": "case",
        "keywords": ["divorce", "petition", "matrimonial", "petitioner", "respondent", "cruelty", "desertion", "dissolution of marriage"],
        "acts": ["Hindu Marriage Act 1955 s.13", "Special Marriage Act 1954", "Divorce Act 1869 (Christians)", "Dissolution of Muslim Marriages Act 1939", "BNSS 2023 s.144 (maintenance)"],
    },
    "maintenance_petition": {
        "name": "Maintenance Petition", "mode": "case",
        "keywords": ["maintenance", "alimony", "interim maintenance", "unable to maintain", "wife", "125 crpc", "144 bnss"],
        "acts": ["BNSS 2023 s.144 (erstwhile CrPC s.125)", "Hindu Marriage Act 1955 ss.24-25", "Hindu Adoptions and Maintenance Act 1956"],
    },
    "child_custody": {
        "name": "Child Custody Petition", "mode": "case",
        "keywords": ["custody", "guardian", "minor child", "welfare of the child", "visitation", "guardianship"],
        "acts": ["Guardians and Wards Act 1890", "Hindu Minority and Guardianship Act 1956"],
    },
    "domestic_violence": {
        "name": "Domestic Violence Complaint", "mode": "case",
        "keywords": ["domestic violence", "aggrieved", "protection order", "residence order", "dowry", "harassment", "498a"],
        "acts": ["Protection of Women from Domestic Violence Act 2005", "BNS 2023 s.85 (cruelty; erstwhile IPC 498A)", "Dowry Prohibition Act 1961"],
    },
    "cheque_bounce": {
        "name": "Cheque Bounce Case (NI Act s.138)", "mode": "case",
        "keywords": ["cheque", "dishonour", "insufficient funds", "138", "negotiable instrument", "bounced", "return memo"],
        "acts": ["Negotiable Instruments Act 1881 ss.138-142", "BNSS 2023"],
    },
    "consumer_complaint": {
        "name": "Consumer Complaint", "mode": "case",
        "keywords": ["consumer", "complaint", "deficiency in service", "unfair trade practice", "commission", "compensation", "refund"],
        "acts": ["Consumer Protection Act 2019"],
    },
    "writ_petition": {
        "name": "Writ Petition (High Court / Supreme Court)", "mode": "case",
        "keywords": ["writ", "mandamus", "certiorari", "habeas corpus", "article 226", "article 32", "petitioner", "respondent state"],
        "acts": ["Constitution of India Articles 226 & 32", "the specific statute/rule challenged"],
    },
    "eviction_suit": {
        "name": "Eviction Suit", "mode": "case",
        "keywords": ["eviction", "ejectment", "arrears of rent", "bona fide requirement", "tenant", "landlord", "possession"],
        "acts": ["the State Rent Control Act", "Transfer of Property Act 1882 s.106", "Code of Civil Procedure 1908"],
    },
    "property_dispute": {
        "name": "Property Dispute / Title Suit", "mode": "case",
        "keywords": ["title", "possession", "partition", "declaration", "injunction", "encroachment", "boundary"],
        "acts": ["Specific Relief Act 1963", "Transfer of Property Act 1882", "Code of Civil Procedure 1908", "Limitation Act 1963"],
    },
    "rti_application": {
        "name": "RTI Application / Reply", "mode": "case",
        "keywords": ["right to information", "rti", "public information officer", "pio", "first appeal", "section 6"],
        "acts": ["Right to Information Act 2005"],
    },

    "general": {
        "name": "Legal Document", "mode": "agreement",
        "keywords": [],
        "acts": ["Indian Contract Act 1872", "the relevant Indian statute"],
    },
}


def detect_document_type(text: str, filename: str) -> tuple[str, str]:
    """Offline fallback classifier (keyword scoring). The LLM classifier in
    classify_document() is preferred; this only runs when that fails."""
    fname = (filename or "").lower()
    sample = (fname + " " + text[:4000]).lower()
    scores: dict[str, int] = {}
    for doc_type, info in DOCUMENT_TEMPLATES.items():
        if doc_type == "general":
            continue
        score = 0
        for kw in info["keywords"]:
            if kw in sample:
                score += 1
            if kw in fname:          # a filename hit is a strong signal
                score += 2
        scores[doc_type] = score
    best = max(scores, key=scores.get) if scores else "general"
    if scores.get(best, 0) == 0:
        best = "general"
    return best, DOCUMENT_TEMPLATES[best]["name"]


def get_doc_mode(doc_type: str) -> str:
    """'agreement' (contract/deed review) or 'case' (court/litigation file)."""
    return DOCUMENT_TEMPLATES.get(doc_type, {}).get("mode", "agreement")


# ── Indian Law KB ─────────────────────────────────────────────────────────────

def get_law_context(doc_type: str) -> str:
    """Indian statutes relevant to a document type (grounds the model's citations)."""
    acts = DOCUMENT_TEMPLATES.get(doc_type, {}).get("acts") or ["Indian Contract Act 1872"]
    return "Relevant Indian laws: " + "; ".join(acts) + "."


# ── LLM-based document classification (preferred) ─────────────────────────────

def _classify_prompt(text: str, filename: str) -> str:
    return f"""You are an expert in Indian law. Identify exactly what this document is.

Return ONLY a JSON object (no markdown, no preamble):
{{
  "document_type": "<precise name, e.g. 'FIR (theft)', 'Divorce Petition under Hindu Marriage Act', 'Rental Agreement', 'Cheque Bounce Complaint (NI Act s.138)', 'Sale Deed', 'Bail Application'>",
  "category": "agreement" | "case",
  "acts": ["<applicable Indian Acts with key sections, e.g. 'Bharatiya Nyaya Sanhita 2023 s.303', 'Hindu Marriage Act 1955 s.13'>"]
}}

Rules:
- category = "case" for FIRs, police/charge sheets, criminal complaints, civil plaints, written statements, petitions (divorce/maintenance/custody), bail applications, summons/notices, legal notices, judgments/orders, consumer/writ/eviction/property-dispute matters.
- category = "agreement" for contracts, deeds (sale/gift/mortgage), leases, wills, powers of attorney, policies, affidavits, receipts.
- For criminal matters, prefer the 2023 codes (BNS / BNSS / BSA) and, where helpful, note the erstwhile IPC/CrPC section in brackets.
- List only Acts that genuinely apply. Never invent section numbers.

Filename: {filename}
Document (beginning):
{text[:4000]}

Return ONLY the JSON object:"""


def parse_classification(raw: str):
    """Parse the classifier output → (doc_type_name, mode, law_context) or None."""
    try:
        data = _extract_json(raw)
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("document_type"):
        return None
    name = str(data["document_type"]).strip()[:90]
    mode = "case" if str(data.get("category", "")).strip().lower().startswith("case") else "agreement"
    acts = data.get("acts") if isinstance(data.get("acts"), list) else []
    acts = [str(a).strip() for a in acts if str(a).strip()]
    law_context = ("Relevant Indian laws: " + "; ".join(acts) + ".") if acts else None
    return name, mode, law_context


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

def _chunk_prompt(doc_type_name: str, law_context: str, chunk_text: str, chunk_index: int = 0, mode: str = "agreement") -> str:
    unit = "charge / prayer / finding / fact" if mode == "case" else "clause / section"
    field_guide = (
        "For case files:\n"
        "- \"title\": e.g. 'Charge 1 — Criminal Breach of Trust', 'Prayer A — Permanent Injunction', 'Fact 3 — Incident on 12/04/2023'.\n"
        "- \"risk_level\": 'high' for severe charges/orders against the reader, 'medium' for uncertain/contested claims, 'low' for procedural/favourable facts.\n"
        "- \"risk_reason\": legal implications under Indian law (cite exact Acts & sections, e.g. BNS 2023 s.316, CPC Order 39, NI Act s.138).\n"
        "- \"beneficial_to_user\": true if this point supports the reader's case or grants them relief; false if it imposes liability or charges them."
        if mode == "case" else
        "For contracts/deeds:\n"
        "- \"title\": descriptive name, e.g. 'Rent & Security Deposit', 'Termination Notice Period'.\n"
        "- \"risk_level\": 'high' if harsh/one-sided against reader, 'medium' if standard, 'low' if protective.\n"
        "- \"beneficial_to_user\": true if protective of reader; false if restrictive or one-sided."
    )

    return f"""{PROMPT_INJECTION_SAFETY_HEADER}
You are a senior Indian lawyer. Extract and analyze every distinct {unit} from the document section below ({doc_type_name}).
{law_context}

IMPORTANT: Provide simple explanations in English, Hindi (Devanagari script), AND the document's own language as specified below.

Work through document section {chunk_index + 1}. Return ONLY a valid JSON array — no explanation, no markdown, no preamble.

Each object represents one {unit} and must have exactly these fields:
{{
  "id": "clause_<number>",
  "title": "Short title (English)",
  "original_text": "Exact text copied from the document, in its ORIGINAL language/script",
  "plain_english": "Simple English explanation (2-3 sentences)",
  "plain_hindi": "Simple Hindi (Devanagari) explanation (2-3 sentences)",
  "plain_source": "Simple explanation in the SAME language as the document. If the document is in English, repeat the English explanation here.",
  "source_language": "the document's language name in English, e.g. Marathi, Telugu, Tamil, Hindi, English",
  "risk_level": "low" | "medium" | "high",
  "risk_score": <1-10>,
  "risk_reason": "...",
  "clause_type": "...",
  "beneficial_to_user": true | false
}}

{field_guide}

Be thorough and precise: capture every distinct item — do not skip, merge, or summarise them together. Keep "original_text" faithful to the document in its original script. Cite exact statutes and section numbers in "risk_reason"; if you are unsure of a section, name only the Act rather than guessing a number. Provide accurate translations (real "plain_hindi" and "plain_source", not transliterations).

<untrusted_document_content>
{chunk_text}
</untrusted_document_content>

Return ONLY the JSON array:"""



def _summary_prompt(doc_type_name: str, law_context: str, clauses_json: str, mode: str = "agreement") -> str:
    if mode == "case":
        guide = (
            "This is a court / case document. Fill the fields as:\n"
            "- \"parties\": each party WITH their role, e.g. 'Ramesh (Complainant/Petitioner)', 'State of Maharashtra (Prosecution)', 'Suresh (Accused/Respondent)'.\n"
            "- \"key_dates\": incident date, FIR/filing date, next hearing date, and any limitation/response deadline.\n"
            "- \"overall_risk\": how serious the reader's overall legal exposure is.\n"
            "- \"risk_summary\": 2-3 plain-English sentences on what the case is about and where the reader stands.\n"
            "- \"high_risk_clauses\": the most serious charges/allegations or adverse findings against the reader.\n"
            "- \"beneficial_clauses\": points in the reader's favour or available defences.\n"
            "- \"your_obligations\": concrete NEXT STEPS for the reader (appear on the hearing date, file reply/bail, respond to the notice within the deadline, etc.).\n"
            "- \"other_party_rights\": what the opposing party / prosecution can seek.\n"
            "Cite the exact Indian Acts and sections; prefer the 2023 codes (BNS/BNSS/BSA) for criminal matters."
        )
    else:
        guide = (
            "This is an agreement/deed. Fill the fields as:\n"
            "- \"parties\": the contracting parties with their role (e.g. 'Landlord', 'Tenant').\n"
            "- \"key_dates\": start/end/renewal/payment dates.\n"
            "- \"overall_risk\": how one-sided/risky the document is for the reader.\n"
            "- \"high_risk_clauses\": the clauses most against the reader.\n"
            "- \"beneficial_clauses\": clauses that protect the reader.\n"
            "- \"your_obligations\": key things the reader must do.\n"
            "- \"other_party_rights\": key rights the other party has."
        )

    return f"""You are a senior Indian lawyer. Based on the extracted points below, write a summary for this {doc_type_name}.
{law_context}

Return ONLY a valid JSON object. No explanation, no markdown.

{guide}

The document may be in English or any Indian language (Hindi, Marathi, Telugu, Tamil, Bengali, Gujarati, Kannada, Malayalam, Punjabi, Odia, Urdu, etc.). Understand it in its original language and set "language" to that language's English name.

Required fields:
{{
  "document_type": "{doc_type_name}",
  "language": "the document's language name in English, e.g. Marathi, Telugu, English",
  "parties": ["..."],
  "key_dates": [{{"label": "Label", "date": "DD/MM/YYYY"}}],
  "overall_risk": "low" | "medium" | "high",
  "risk_summary": "2-3 sentence plain English summary",
  "high_risk_clauses": ["..."],
  "beneficial_clauses": ["..."],
  "your_obligations": ["..."],
  "other_party_rights": ["..."],
  "total_clauses": <number>,
  "high_risk_count": <number>,
  "medium_risk_count": <number>,
  "low_risk_count": <number>
}}

Extracted points:
{clauses_json}

Return ONLY the JSON object:"""


def _format_analysis_context(analysis_summary: dict | None) -> str:
    """Compact grounding block built from the document's saved analysis."""
    if not isinstance(analysis_summary, dict):
        return ""
    lines: list[str] = []
    if analysis_summary.get("risk_summary"):
        lines.append(f"- Overall: {analysis_summary['risk_summary']} (overall risk: {analysis_summary.get('overall_risk', 'n/a')})")
    def _take(key, label, n):
        vals = analysis_summary.get(key) or []
        if isinstance(vals, list) and vals:
            lines.append(f"- {label}: " + "; ".join(str(v) for v in vals[:n]))
    _take("high_risk_clauses", "Most serious/adverse points", 4)
    _take("beneficial_clauses", "Points in the reader's favour", 3)
    _take("your_obligations", "Reader's obligations / next steps", 4)
    _take("other_party_rights", "Opposing party can seek", 3)
    if not lines:
        return ""
    return "Key findings from the prior analysis of this document:\n" + "\n".join(lines)


def _format_history(history: list | None) -> str:
    """Recent conversation turns so follow-up questions stay coherent."""
    if not history:
        return ""
    turns = []
    for m in history[-6:]:
        role = "User" if m.get("role") == "user" else "Assistant"
        content = str(m.get("content", "")).strip().replace("\n", " ")
        if content:
            turns.append(f"{role}: {content[:400]}")
    return ("Recent conversation:\n" + "\n".join(turns)) if turns else ""


def _chat_prompt(
    doc_text: str,
    question: str,
    doc_type_name: str | None = None,
    law_context: str | None = None,
    analysis_summary: dict | None = None,
    history: list | None = None,
) -> str:
    doc_label = doc_type_name or "legal document"
    laws = law_context or "Relevant Indian laws: Indian Contract Act 1872."
    analysis_block = _format_analysis_context(analysis_summary)
    history_block = _format_history(history)

    context_parts = [f"Document type: {doc_label}", laws]
    if analysis_block:
        context_parts.append(analysis_block)
    if history_block:
        context_parts.append(history_block)
    context = "\n\n".join(context_parts)

    return f"""{PROMPT_INJECTION_SAFETY_HEADER}
You are SmartLegal AI — a knowledgeable Indian legal assistant explaining a {doc_label} to an ordinary citizen (not a lawyer).

{context}

How to answer:
1. Start with a direct, plain-language answer to the exact question (1-2 sentences).
2. "In this document" — point to the specific clause / point / fact that applies, quoting a short phrase where useful. If the document does not cover it, say so honestly.
3. "Under Indian law" — cite the EXACT statute and section that governs this (e.g. "Bharatiya Nyaya Sanhita 2023 s.303 — theft", "Hindu Marriage Act 1955 s.13(1)(ia)", "Negotiable Instruments Act 1881 s.138", "Transfer of Property Act 1882 s.106"). For criminal matters prefer the 2023 codes (BNS/BNSS/BSA) and note the erstwhile IPC/CrPC section in brackets. NEVER invent or guess a section number — if unsure, name only the Act.
4. "What you can do" — 2-4 concrete, practical next steps (e.g. reply within the notice period, gather documents, negotiate a clause, consult a lawyer for X).

Rules:
- Base your answer ONLY on the document above and well-established Indian law. Do not fabricate facts, parties, amounts, dates, or sections.
- Be specific and genuinely useful — around 250-400 words. Use short paragraphs or bullets.
- Format in clean Markdown. Use a Markdown table only for genuinely tabular content, kept to 2-3 short columns so it reads well on mobile; always include the header separator row (| --- | --- |) and keep every row's pipe count identical.
- Simple, clear English. If the user asks in Hindi or asks for Hindi, answer in Hindi.
- End with exactly this line: "Note: This is AI-assisted analysis, not formal legal advice. Consult a qualified advocate before acting."

<untrusted_document_content>
{doc_text[:12000]}
</untrusted_document_content>

<user_question>
{question}
</user_question>

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
    mode = get_doc_mode(doc_type)

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

    # ── LLM classification (preferred over keyword scoring) ──
    try:
        raw_cls = await _call_gemini(_classify_prompt(text, filename))
        classified = parse_classification(raw_cls)
        if classified:
            doc_type_name, mode, law_from_llm = classified
            if law_from_llm:
                law_context = law_from_llm
            print(f"[gemini] LLM classified as: {doc_type_name} (mode={mode})")
    except Exception as exc:
        print(f"[gemini] Classification step failed, using keyword detection: {exc}")

    # ── Text-Based PDF Analysis (chunked) ──
    from services.pdf_parser import split_into_chunks

    chunks = split_into_chunks(text, max_chars=12000)
    print(f"[gemini] Split text into {len(chunks)} chunks")

    all_clauses = []
    chunk_errors = []

    if not chunks:
        raise RuntimeError("Gemini analysis failed: no text chunks were available.")

    for i, chunk in enumerate(chunks):
        prompt = _chunk_prompt(doc_type_name, law_context, chunk["text"], i, mode)
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
        doc_type_name, law_context, json.dumps(all_clauses[:20], indent=2), mode
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


async def answer_question_about_document(
    doc_text: str,
    question: str,
    doc_type_name: str | None = None,
    law_context: str | None = None,
    analysis_summary: dict | None = None,
    history: list | None = None,
) -> str:
    """Answer a user question grounded in document text + Indian law using Gemini."""
    prompt = _chat_prompt(doc_text, question, doc_type_name, law_context, analysis_summary, history)
    try:
        return await _call_gemini(prompt)
    except Exception as exc:
        raise RuntimeError(f"AI failed to answer: {exc}") from exc
