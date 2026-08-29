"""
yojana_blog_service.py — Autonomous AI Blog Generation & Citizen Guide Service.

Generates plain-language, SEO-optimized citizen guides with verified official
government links (.gov.in) and image artwork references whenever new schemes
are ingested or queried.
"""

import json
import re
import uuid
from datetime import datetime
from services.gemini_service import _extract_json

SEED_BLOGS = [

    {
        "id": "blog_pm_kisan_guide",
        "scheme_id": "sch_pm_kisan",
        "title": "PM Kisan Samman Nidhi 2026: Complete Guide to ₹6,000 Payout & e-KYC",
        "slug": "pm-kisan-samman-nidhi-2026-guide",
        "summary": "Everything you need to know about receiving ₹6,000 annual income support directly into your bank account under PM Kisan, including e-KYC registration and 7/12 land record linking.",
        "image_url": "/illustrations/pm_kisan_banner.jpg",
        "content_markdown": """# PM Kisan Samman Nidhi Yojana 2026: Complete Citizen Guide

![PM Kisan Scheme Direct Income Support](/illustrations/pm_kisan_banner.jpg)

The **Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)** is a landmark Central Sector Scheme designed to provide income support to all landholding farmer families across India.

## Key Scheme Highlights

* **Total Annual Payout:** ₹6,000 per year transferred directly to bank accounts (DBT).
* **Installment Schedule:** 3 equal installments of ₹2,000 every 4 months.
* **Funding:** 100% funded by the Government of India.

## Who is Eligible?

All landholding farmer families who own cultivable land in their names are eligible. 

### Key Eligibility Rules:
1. Must hold registered agricultural land.
2. Must have an active bank account linked with Aadhaar.
3. Must complete mandatory **e-KYC** on the PM Kisan portal.

## Excluded Categories
* Institutional landholders.
* Farmer families with any member paying Income Tax in the last assessment year.
* Serving or retired officers of Central/State government ministries.

## Required Documents Checklist

- [x] Aadhaar Card linked with active mobile number
- [x] Land Holding Certificate (7/12 Extract / Khasra / Khatoni)
- [x] Active Savings Bank Account details (Aadhaar Seeded)
- [x] e-KYC Verification receipt

## Step-by-Step Online Application Process

1. Visit the **Official PM Kisan Portal**: [pmkisan.gov.in](https://pmkisan.gov.in)
2. Click on **'New Farmer Registration'** on the homepage.
3. Enter your 12-digit Aadhaar number and select your State.
4. Upload your Land Record details (Survey/Khasra number and area in hectares).
5. Submit the application and note down your Farmer Registration Reference ID.

---
*Note: Always verify scheme details on the official government website [pmkisan.gov.in](https://pmkisan.gov.in).*""",
        "official_links_json": json.dumps([
            {"label": "PM Kisan Official Portal", "url": "https://pmkisan.gov.in"},
            {"label": "PM Kisan e-KYC Portal", "url": "https://pmkisan.gov.in/aadharkyc.aspx"},
            {"label": "Check Beneficiary Status", "url": "https://pmkisan.gov.in/BeneficiaryStatus.aspx"}
        ]),
        "published_at": datetime.utcnow().isoformat()
    },
    {
        "id": "blog_abha_card_guide",
        "scheme_id": "sch_abha_card",
        "title": "ABHA Health Card 2026: How to Create Your 14-Digit Health ID Online",
        "slug": "abha-health-card-creation-guide-2026",
        "summary": "Step-by-step guide to creating your unique 14-digit Ayushman Bharat Health Account (ABHA) card online using Aadhaar for seamless digital medical records.",
        "image_url": "/illustrations/abha_card_banner.jpg",
        "content_markdown": """# Ayushman Bharat Health Account (ABHA Card): Instant 14-Digit Digital Health ID

![ABHA Health Card Digital Health ID](/illustrations/abha_card_banner.jpg)

The **ABHA Card** (Ayushman Bharat Health Account) is a unique 14-digit digital health ID issued under the **Ayushman Bharat Digital Mission (ABDM)**.

## Why Do You Need an ABHA Card?

* **Unified Health Records:** Store lab reports, prescriptions, and diagnostic tests digitally in one place.
* **Paperless Hospital Visits:** Share your medical history securely with doctors across empaneled hospitals without carrying paper files.
* **Consent-Based Privacy:** Medical records are shared only when you give explicit OTP consent.

## Step-by-Step ABHA Card Creation (2 Minutes)

1. Go to the official ABDM portal: [abha.abdm.gov.in](https://abha.abdm.gov.in)
2. Click on **'Create ABHA Number'**.
3. Choose **'Create using Aadhaar'** (Recommended).
4. Enter your 12-digit Aadhaar number and submit the OTP sent to your Aadhaar-linked mobile.
5. Download your digital ABHA QR Card instantly.

---
*Official Government Portal: [abha.abdm.gov.in](https://abha.abdm.gov.in)*""",
        "official_links_json": json.dumps([
            {"label": "ABHA Card Creation Portal", "url": "https://abha.abdm.gov.in"},
            {"label": "Ayushman Bharat Digital Mission", "url": "https://abdm.gov.in"}
        ]),
        "published_at": datetime.utcnow().isoformat()
    },
    {
        "id": "blog_ayushman_bharat_guide",
        "scheme_id": "sch_ayushman_bharat",
        "title": "Ayushman Bharat PM-JAY 2026: ₹5 Lakh Free Cashless Hospital Treatment",
        "slug": "ayushman-bharat-pmjay-5-lakh-free-treatment-guide",
        "summary": "Complete guide to getting your Ayushman Card for ₹5 Lakh annual free cashless hospital cover across all government and empaneled private hospitals.",
        "image_url": "/illustrations/ayushman_bharat_banner.jpg",
        "content_markdown": """# Ayushman Bharat PM-JAY: ₹5 Lakh Health Cover per Family

![Ayushman Bharat Free Cashless Hospitalization](/illustrations/ayushman_bharat_banner.jpg)

The **Pradhan Mantri Jan Arogya Yojana (PM-JAY)** is the world's largest government-funded healthcare scheme, providing a health cover of ₹5 Lakh per family per year for secondary and tertiary care hospitalization.

## Benefits Included

* **Cashless Treatment:** Zero out-of-pocket expenses at empaneled public and private hospitals.
* **Pre & Post Hospitalization:** Covers 3 days of pre-hospitalization and 15 days of post-hospitalization diagnostic tests and medicines.
* **Pre-existing Conditions:** All pre-existing medical conditions are covered from Day 1.

## How to Check Eligibility

1. Visit [pmjay.gov.in](https://pmjay.gov.in) and click **'Am I Eligible'**.
2. Enter your mobile number and select your State.
3. Search by Ration Card number, Name, or HHD number.

---
*Official Government Portal: [pmjay.gov.in](https://pmjay.gov.in)*""",
        "official_links_json": json.dumps([
            {"label": "PM-JAY Official Portal", "url": "https://pmjay.gov.in"},
            {"label": "Find Empaneled Hospitals", "url": "https://hospitals.pmjay.gov.in"}
        ]),
        "published_at": datetime.utcnow().isoformat()
    },
    {
        "id": "blog_ladli_behna_guide",
        "scheme_id": "sch_ladli_behna_mp",
        "title": "Ladli Behna Yojana 2026: ₹1,250 Monthly Financial Support for Women",
        "slug": "cm-ladli-behna-yojana-mp-complete-guide",
        "summary": "Guide for eligible women in Madhya Pradesh to receive ₹1,250 per month directly into DBT-linked bank accounts under CM Ladli Behna Yojana.",
        "image_url": "/illustrations/ladli_behna_banner.jpg",
        "content_markdown": """# Chief Minister Ladli Behna Yojana: Empowering Women in MP

![Ladli Behna Women Financial Empowerment](/illustrations/ladli_behna_banner.jpg)

The **CM Ladli Behna Yojana** provides ₹1,250 monthly direct financial assistance to eligible women in Madhya Pradesh to foster economic independence and family health.

## Eligibility Criteria

1. Resident of Madhya Pradesh.
2. Married, widowed, divorced, or abandoned women aged between 21 and 60 years.
3. Annual family income below ₹2.5 Lakhs.

---
*Official Government Portal: [cmladlibehna.mp.gov.in](https://cmladlibehna.mp.gov.in)*""",
        "official_links_json": json.dumps([
            {"label": "Ladli Behna Official Portal", "url": "https://cmladlibehna.mp.gov.in"}
        ]),
        "published_at": datetime.utcnow().isoformat()
    }
]


def _slugify(text: str) -> str:
    """Converts a title string into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


async def seed_default_blogs_if_empty(db) -> int:
    """Auto-populates and updates baseline AI citizen blogs in database."""
    try:
        inserted = 0
        for b in SEED_BLOGS:
            await db.execute(
                """INSERT INTO yojana_blogs (
                    id, scheme_id, title, slug, summary, content_markdown,
                    image_url, official_links_json, published_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    content_markdown = EXCLUDED.content_markdown,
                    image_url = EXCLUDED.image_url,
                    official_links_json = EXCLUDED.official_links_json""",
                b["id"], b["scheme_id"], b["title"], b["slug"], b["summary"],
                b["content_markdown"], b["image_url"], b["official_links_json"], b["published_at"]
            )
            inserted += 1
        print(f"[yojana_blog] Synced {inserted} AI citizen blogs with photographs in database")
        return inserted
    except Exception as exc:
        print(f"[yojana_blog] Seeding blogs failed: {exc}")
        return 0



async def generate_ai_blog_for_scheme(scheme: dict) -> dict:
    """
    Uses Groq/Gemini LLM to generate an SEO-optimized markdown article
    explaining scheme background, benefits, step-by-step application, and official links.
    """
    from services.groq_service import _call_groq

    prompt = f"""You are a senior Indian Civic Tech Journalist writing a comprehensive, friendly citizen guide for a government scheme.

SCHEME DETAILS:
Title: {scheme.get('title')}
Category: {scheme.get('category')}
Level: {scheme.get('government_level')} ({scheme.get('state_name')})
Official Portal: {scheme.get('official_portal_url')}
Summary: {scheme.get('summary_english')}
Benefits: {json.dumps(scheme.get('benefits', []))}
Required Documents: {json.dumps(scheme.get('required_docs', []))}

Generate a detailed Markdown blog post. Return ONLY valid JSON in EXACTLY this shape:
{{
  "title": "{scheme.get('title')} 2026: Complete Citizen Guide & Application Steps",
  "summary": "Plain English 2-sentence summary",
  "content_markdown": "# Title\\n\\nComprehensive guide in markdown format with section headings, key highlights, eligibility checklist, and step-by-step online application instructions.",
  "official_links": [
    {{"label": "Official Portal", "url": "{scheme.get('official_portal_url')}"}}
  ]
}}"""

    try:
        raw = await _call_groq(prompt, max_tokens=2200)
        parsed = _extract_json(raw)
        if isinstance(parsed, dict) and parsed.get("title"):
            slug = _slugify(parsed["title"])
            return {
                "id": f"blog_{uuid.uuid4().hex[:8]}",
                "scheme_id": scheme.get("id"),
                "title": parsed["title"],
                "slug": slug,
                "summary": parsed.get("summary", scheme.get("summary_english", "")),
                "content_markdown": parsed.get("content_markdown", f"# {parsed['title']}"),
                "image_url": f"/illustrations/{scheme.get('category', 'healthcare').lower()}_banner.png",
                "official_links_json": json.dumps(parsed.get("official_links", [{"label": "Official Portal", "url": scheme.get("official_portal_url")}])),
                "published_at": datetime.utcnow().isoformat()
            }
    except Exception as exc:
        print(f"[yojana_blog] AI blog generation failed: {exc}")

    # Fallback return
    slug = _slugify(scheme.get("title", "Government Scheme Guide"))
    return {
        "id": f"blog_{uuid.uuid4().hex[:8]}",
        "scheme_id": scheme.get("id"),
        "title": f"{scheme.get('title')} Guide 2026",
        "slug": slug,
        "summary": scheme.get("summary_english", ""),
        "content_markdown": f"# {scheme.get('title')}\n\n{scheme.get('summary_english')}\n\nOfficial Portal: [{scheme.get('official_portal_url')}]({scheme.get('official_portal_url')})",
        "image_url": "/illustrations/service_banner.png",
        "official_links_json": json.dumps([{"label": "Official Portal", "url": scheme.get("official_portal_url", "https://myscheme.gov.in")}]),
        "published_at": datetime.utcnow().isoformat()
    }
