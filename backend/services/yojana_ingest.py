"""
yojana_ingest.py — Automated Scheme Ingestion Service.

Handles automated seeding and LLM-powered extraction of Indian Central & State
Government Schemes (e.g. PM-KISAN, PM Jan Dhan, ABHA Card, Ayushman Bharat,
Mahatma Jyotirao Phule Jan Arogya Yojana, Ladli Behna, etc.).
"""

import json
import uuid
from datetime import datetime
from services.gemini_service import _extract_json

SEED_SCHEMES = [
    {
        "id": "sch_pm_kisan",
        "scheme_code": "PM_KISAN",
        "title": "PM Kisan Samman Nidhi Yojana",
        "government_level": "central",
        "state_name": "ALL",
        "category": "Agriculture",
        "summary_english": "Provides income support of ₹6,000 per year in 3 equal installments of ₹2,000 directly into the bank accounts of all landholding farmer families across India.",
        "summary_hindi": "सभी भूमिधारक किसान परिवारों को प्रति वर्ष ₹6,000 की आय सहायता 3 समान किस्तों में सीधे बैंक खाते में प्रदान की जाती है।",
        "benefits_json": json.dumps([
            "₹6,000 per year direct cash transfer via DBT",
            "3 installments of ₹2,000 every 4 months",
            "100% Central Government funded"
        ]),
        "eligibility_json": json.dumps({
            "occupations": ["farmer"],
            "income_max": 800000,
            "min_age": 18,
            "max_age": 75,
            "requires_landholding": True,
            "max_land_acres": 10.0,
            "excluded_categories": ["institutional_landholders", "taxpayer_farmers"]
        }),
        "required_docs_json": json.dumps([
            "Aadhaar Card linked with mobile number",
            "Land Holding Certificate / 7-12 Extract / Khasra",
            "Active Savings Bank Account Details",
            "e-KYC Verification"
        ]),
        "official_portal_url": "https://pmkisan.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "sch_pm_jandhan",
        "scheme_code": "PM_JANDHAN",
        "title": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "government_level": "central",
        "state_name": "ALL",
        "category": "Finance",
        "summary_english": "National Mission for Financial Inclusion providing zero-balance savings accounts, RuPay debit cards, ₹2 Lakh accidental insurance cover, and ₹10,000 overdraft facility.",
        "summary_hindi": "शून्य-शेष बचत खाते, रूपे डेबिट कार्ड, ₹2 लाख दुर्घटना बीमा और ₹10,000 ओवरड्राफ्ट सुविधा प्रदान करने वाला वित्तीय समावेशन का राष्ट्रीय मिशन।",
        "benefits_json": json.dumps([
            "Zero minimum balance account",
            "₹2,000,000 (₹2 Lakh) Accidental Death Insurance cover",
            "Overdraft facility up to ₹10,000 per household",
            "Direct Benefit Transfer (DBT) compatibility"
        ]),
        "eligibility_json": json.dumps({
            "occupations": ["farmer", "student", "salaried", "unemployed", "self_employed", "construction_worker"],
            "income_max": 1000000,
            "min_age": 10,
            "max_age": 75
        }),
        "required_docs_json": json.dumps([
            "Aadhaar Card OR Passport / Voter ID / Driving License",
            "Passport Size Photograph",
            "Mobile Number for SMS alerts"
        ]),
        "official_portal_url": "https://pmjdy.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "sch_abha_card",
        "scheme_code": "ABHA_CARD",
        "title": "Ayushman Bharat Health Account (ABHA Card)",
        "government_level": "central",
        "state_name": "ALL",
        "category": "Healthcare",
        "summary_english": "Creates a unique 14-digit digital health ID that securely links all your medical records, lab reports, prescriptions, and health insurance claims digitally across India.",
        "summary_hindi": "एक अद्वितीय 14-अंकीय डिजिटल स्वास्थ्य आईडी जो आपके सभी मेडिकल रिकॉर्ड, लैब रिपोर्ट और बीमा दावों को डिजिटल रूप से सुरक्षित रूप से जोड़ती है।",
        "benefits_json": json.dumps([
            "14-digit unique Ayushman Bharat Health Account ID",
            "Seamless digital sharing of lab reports and prescriptions",
            "100% paperless medical history at hospitals",
            "Integration with Tele-consultation services"
        ]),
        "eligibility_json": json.dumps({
            "occupations": ["farmer", "student", "salaried", "unemployed", "self_employed", "construction_worker"],
            "income_max": 9999999,
            "min_age": 0,
            "max_age": 100
        }),
        "required_docs_json": json.dumps([
            "Aadhaar Card OR Driving License",
            "Aadhaar-linked Mobile Number for OTP"
        ]),
        "official_portal_url": "https://abha.abdm.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "sch_ayushman_bharat",
        "scheme_code": "AYUSHMAN_BHARAT",
        "title": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "government_level": "central",
        "state_name": "ALL",
        "category": "Healthcare",
        "summary_english": "World's largest government-funded health health insurance scheme providing ₹5 Lakhs cashless health coverage per family per year for secondary and tertiary hospital care.",
        "summary_hindi": "द्वितीयक और तृतीयक अस्पताल देखभाल के लिए प्रति परिवार प्रति वर्ष ₹5 लाख का कैशलेस स्वास्थ्य कवर प्रदान करने वाली दुनिया की सबसे बड़ी योजना।",
        "benefits_json": json.dumps([
            "₹5,000,000 (₹5 Lakh) health cover per family per year",
            "Cashless treatment at over 27,000 empaneled hospitals",
            "Covers 1,949 medical procedures including pre & post hospitalization"
        ]),
        "eligibility_json": json.dumps({
            "occupations": ["farmer", "unemployed", "construction_worker", "self_employed"],
            "income_max": 300000,
            "min_age": 0,
            "max_age": 100,
            "requires_bpl_or_secc": True
        }),
        "required_docs_json": json.dumps([
            "Ayushman Card / Ration Card / PM-JAY Letter",
            "Aadhaar Card for identity verification"
        ]),
        "official_portal_url": "https://pmjay.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "sch_mjpjay_maha",
        "scheme_code": "MAHATMA_JYOTIBA_PHULE",
        "title": "Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)",
        "government_level": "state",
        "state_name": "Maharashtra",
        "category": "Healthcare",
        "summary_english": "Maharashtra state flagship health insurance scheme providing cashless medical treatment up to ₹5 Lakhs per family per year across empaneled hospitals in Maharashtra.",
        "summary_hindi": "महाराष्ट्र सरकार की प्रमुख स्वास्थ्य योजना जो महाराष्ट्र के सूचीबद्ध अस्पतालों में प्रति परिवार ₹5 लाख तक का कैशलेस इलाज प्रदान करती है।",
        "benefits_json": json.dumps([
            "₹5,00,000 cashless health insurance cover per family per year",
            "Covers 996 medical and surgical procedures",
            "Free medicines, diagnostics, and doctor consultation during hospital stay"
        ]),
        "eligibility_json": json.dumps({
            "occupations": ["farmer", "unemployed", "construction_worker", "self_employed", "salaried"],
            "income_max": 250000,
            "min_age": 0,
            "max_age": 100,
            "states": ["Maharashtra"],
            "ration_card_types": ["yellow", "orange", "antyodaya"]
        }),
        "required_docs_json": json.dumps([
            "Yellow or Orange Ration Card / Annapurna Card",
            "Aadhaar Card or Voter ID",
            "Maharashtra Domicile Certificate / Income Certificate"
        ]),
        "official_portal_url": "https://www.jeeconvani.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "sch_ladli_behna_mp",
        "scheme_code": "LADLI_BEHNA",
        "title": "Chief Minister Ladli Behna Yojana",
        "government_level": "state",
        "state_name": "Madhya Pradesh",
        "category": "Women",
        "summary_english": "Direct monthly financial assistance of ₹1,250 per month transferred directly to eligible married, widowed, or divorced women aged 21 to 60 in Madhya Pradesh.",
        "summary_hindi": "मध्य प्रदेश की 21 से 60 वर्ष की पात्र विवाहित, विधवा या परित्यक्ता महिलाओं के खाते में प्रति माह ₹1,250 की प्रत्यक्ष वित्तीय सहायता।",
        "benefits_json": json.dumps([
            "₹1,250 per month direct bank transfer (DBT)",
            "₹15,000 total annual financial support for women empowerment"
        ]),
        "eligibility_json": json.dumps({
            "gender": "female",
            "min_age": 21,
            "max_age": 60,
            "income_max": 250000,
            "states": ["Madhya Pradesh"],
            "marital_status": ["married", "widowed", "divorced"]
        }),
        "required_docs_json": json.dumps([
            "Samagra Family ID & Member ID",
            "Aadhaar Card linked with Bank Account & DBTE",
            "Income Self-Declaration"
        ]),
        "official_portal_url": "https://cmladlibehna.mp.gov.in",
        "last_updated_at": datetime.utcnow().isoformat()
    }
]


async def seed_default_schemes_if_empty(db) -> int:
    """Auto-populates default Central & State schemes if database table is empty."""
    try:
        count_row = await db.fetchrow("SELECT COUNT(*) as cnt FROM yojana_schemes")
        count = count_row["cnt"] if count_row else 0
        if count > 0:
            return count

        inserted = 0
        for s in SEED_SCHEMES:
            await db.execute(
                """INSERT INTO yojana_schemes (
                    id, scheme_code, title, government_level, state_name, category,
                    summary_english, summary_hindi, benefits_json, eligibility_json,
                    required_docs_json, official_portal_url, last_updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (scheme_code) DO NOTHING""",
                s["id"], s["scheme_code"], s["title"], s["government_level"], s["state_name"],
                s["category"], s["summary_english"], s["summary_hindi"], s["benefits_json"],
                s["eligibility_json"], s["required_docs_json"], s["official_portal_url"], s["last_updated_at"]
            )
            inserted += 1
        print(f"[yojana_ingest] Seeded {inserted} official Indian schemes into database")
        return inserted
    except Exception as exc:
        print(f"[yojana_ingest] Seeding failed: {exc}")
        return 0


async def parse_scheme_notice_with_llm(raw_text: str, filename: str = "notice.txt") -> dict:
    """
    Uses Groq/Gemini LLM to extract structured scheme details, rules, and portal URLs
    from raw government press release text or gazette PDF text.
    """
    from services.groq_service import _call_groq

    prompt = f"""You are an expert Indian Government Policy Analyst. Parse the following official press release / gazette text for a Central or State scheme and extract structured details.

GOVERNMENT NOTICE TEXT:
{raw_text[:8000]}

Return ONLY valid JSON (no markdown prose outside JSON) in EXACTLY this structure:
{{
  "scheme_code": "SHORT_UNIQUE_CODE",
  "title": "Full Official Scheme Name",
  "government_level": "central|state",
  "state_name": "State Name or ALL",
  "category": "Agriculture|Healthcare|Finance|Women|Education|Housing|Employment",
  "summary_english": "2-3 sentence plain English summary of benefits",
  "summary_hindi": "2-3 sentence simple Hindi explanation",
  "benefits": ["bullet 1", "bullet 2"],
  "eligibility": {{
    "occupations": ["farmer", "student", "salaried", "unemployed", "self_employed", "construction_worker"],
    "income_max": 300000,
    "min_age": 18,
    "max_age": 60,
    "gender": "all|female|male",
    "requires_landholding": false
  }},
  "required_docs": ["Aadhaar Card", "Bank Account", "Income Certificate"],
  "official_portal_url": "https://official.gov.in"
}}"""

    try:
        raw_resp = await _call_groq(prompt, max_tokens=1800)
        data = _extract_json(raw_resp)
        if isinstance(data, dict) and data.get("title"):
            return data
    except Exception as exc:
        print(f"[yojana_ingest] LLM parsing failed: {exc}")

    # Fallback default dict
    return {
        "scheme_code": f"SCH_{uuid.uuid4().hex[:6].upper()}",
        "title": filename.replace(".pdf", "").replace("_", " ").title(),
        "government_level": "central",
        "state_name": "ALL",
        "category": "Healthcare",
        "summary_english": raw_text[:300],
        "summary_hindi": "सरकारी योजना विवरण",
        "benefits": ["Government financial & civic support"],
        "eligibility": {"min_age": 18, "income_max": 800000},
        "required_docs": ["Aadhaar Card", "Bank Account Details"],
        "official_portal_url": "https://myscheme.gov.in"
    }
