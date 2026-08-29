"""
yojana.py — API Router for Jan-Yojana Central & State Government Schemes.
"""

import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from database import get_db
from limiter import limiter
from services.yojana_ingest import seed_default_schemes_if_empty, parse_scheme_notice_with_llm

router = APIRouter()


class IngestNoticeRequest(BaseModel):
    text: str
    filename: str = "official_notice.txt"


class SchemeMatchRequest(BaseModel):
    state: str = "ALL"
    district: str | None = None
    age: int = 25
    gender: str = "all"                     # "male", "female", "all"
    occupation: str = "salaried"             # "farmer", "student", "salaried", "unemployed", "self_employed", "construction_worker"
    annual_income: int = 250000              # Annual family income in Rs.
    category: str = "General"                # "General", "OBC", "SC", "ST", "Minorities", "BPL"
    land_holding_acres: float = 0.0
    is_pregnant_or_lactating: bool = False
    is_disabled: bool = False


def evaluate_scheme_eligibility(scheme: dict, req: SchemeMatchRequest) -> dict:
    """
    Rule Evaluation Engine: Compares citizen profile against scheme criteria
    and computes Match %, Status (eligible/partial/ineligible), & Gap Analysis.
    """
    el = scheme.get("eligibility", {})
    score = 100
    gaps = []

    # 1. Income Check
    income_max = el.get("income_max")
    if income_max and req.annual_income > income_max:
        penalty = 35
        score -= penalty
        gaps.append(f"Family annual income exceeds scheme limit of ₹{income_max:,}")

    # 2. Age Check
    min_age = el.get("min_age", 0)
    max_age = el.get("max_age", 100)
    if req.age < min_age or req.age > max_age:
        score -= 30
        gaps.append(f"Age requirement is between {min_age} and {max_age} years (Your age: {req.age})")

    # 3. Gender Check
    scheme_gender = str(el.get("gender", "all")).lower()
    if scheme_gender in ("female", "male") and req.gender.lower() != "all":
        if req.gender.lower() != scheme_gender:
            score = 0
            gaps.append(f"Scheme is exclusively for {scheme_gender.capitalize()} beneficiaries")

    # 4. Occupation Check
    valid_occ = el.get("occupations", [])
    if valid_occ and req.occupation.lower() not in [o.lower() for o in valid_occ]:
        score -= 25
        gaps.append(f"Targeted primarily for: {', '.join([o.replace('_', ' ').capitalize() for o in valid_occ])}")

    # 5. State Residency Check
    allowed_states = [s.lower() for s in el.get("states", [])]
    if allowed_states and "all" not in allowed_states:
        if req.state.lower() != "all" and req.state.lower() not in allowed_states:
            score -= 40
            gaps.append(f"Applicable only for residents of: {', '.join([s.capitalize() for s in el.get('states', [])])}")

    # 6. Landholding Check
    if el.get("requires_landholding") and req.land_holding_acres <= 0:
        score -= 35
        gaps.append("Requires registered agricultural landholding")

    max_land = el.get("max_land_acres")
    if max_land and req.land_holding_acres > max_land:
        score -= 20
        gaps.append(f"Landholding exceeds maximum limit of {max_land} acres")

    final_score = max(0, min(100, score))
    if final_score >= 80:
        status = "eligible"
    elif final_score >= 40:
        status = "partial"
    else:
        status = "ineligible"

    return {
        "scheme": scheme,
        "match_score": final_score,
        "status": status,
        "gap_analysis": gaps,
        "benefits": scheme.get("benefits", []),
        "required_docs": scheme.get("required_docs", []),
        "official_portal_url": scheme.get("official_portal_url", "https://myscheme.gov.in")
    }



@router.get("/schemes")
async def list_schemes(
    category: str | None = Query(None, description="Filter by category e.g. Healthcare, Agriculture"),
    state: str | None = Query(None, description="Filter by state e.g. Maharashtra, Madhya Pradesh"),
    level: str | None = Query(None, description="Filter by level e.g. central, state"),
    db=Depends(get_db)
):
    """Retrieve active central & state government schemes with optional filters."""
    await seed_default_schemes_if_empty(db)

    query = "SELECT * FROM yojana_schemes WHERE 1=1"
    params = []
    param_idx = 1

    if category and category.lower() != "all":
        query += f" AND LOWER(category) = ${param_idx}"
        params.append(category.lower())
        param_idx += 1

    if level and level.lower() != "all":
        query += f" AND LOWER(government_level) = ${param_idx}"
        params.append(level.lower())
        param_idx += 1

    if state and state.lower() != "all":
        query += f" AND (LOWER(state_name) = ${param_idx} OR LOWER(state_name) = 'all')"
        params.append(state.lower())
        param_idx += 1

    query += " ORDER BY title ASC"

    rows = await db.fetch(query, *params)
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["benefits"] = json.loads(item.get("benefits_json") or "[]")
            item["eligibility"] = json.loads(item.get("eligibility_json") or "{}")
            item["required_docs"] = json.loads(item.get("required_docs_json") or "[]")
        except Exception:
            item["benefits"] = []
            item["eligibility"] = {}
            item["required_docs"] = []
        results.append(item)

    return {"count": len(results), "schemes": results}


@router.get("/schemes/{scheme_id}")
async def get_scheme_details(scheme_id: str, db=Depends(get_db)):
    """Fetch detailed scheme roadmap and application details."""
    row = await db.fetchrow("SELECT * FROM yojana_schemes WHERE id = $1 OR scheme_code = $1", scheme_id)
    if not row:
        raise HTTPException(status_code=404, detail="Government scheme not found.")

    item = dict(row)
    try:
        item["benefits"] = json.loads(item.get("benefits_json") or "[]")
        item["eligibility"] = json.loads(item.get("eligibility_json") or "{}")
        item["required_docs"] = json.loads(item.get("required_docs_json") or "[]")
    except Exception:
        item["benefits"] = []
        item["eligibility"] = {}
        item["required_docs"] = []

    return {"scheme": item}


@router.post("/ingest-notice")
@limiter.limit("5/minute")
async def ingest_official_notice(
    request: Request,
    req: IngestNoticeRequest,
    db=Depends(get_db)
):
    """
    Automated ingestion endpoint: Parses official press release / gazette text
    using Groq/Gemini LLM and saves structured scheme into database.
    """
    if len(req.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Notice text is too short to parse.")

    parsed = await parse_scheme_notice_with_llm(req.text, req.filename)
    scheme_id = f"sch_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    scheme_code = parsed.get("scheme_code", f"SCH_{uuid.uuid4().hex[:6]}").upper()
    title = parsed.get("title", "Official Government Scheme")
    government_level = parsed.get("government_level", "central")
    state_name = parsed.get("state_name", "ALL")
    category = parsed.get("category", "Healthcare")
    summary_eng = parsed.get("summary_english", "Government scheme details")
    summary_hin = parsed.get("summary_hindi", "सरकारी योजना विवरण")
    benefits_str = json.dumps(parsed.get("benefits", []))
    eligibility_str = json.dumps(parsed.get("eligibility", {}))
    docs_str = json.dumps(parsed.get("required_docs", []))
    portal_url = parsed.get("official_portal_url", "https://myscheme.gov.in")

    await db.execute(
        """INSERT INTO yojana_schemes (
            id, scheme_code, title, government_level, state_name, category,
            summary_english, summary_hindi, benefits_json, eligibility_json,
            required_docs_json, official_portal_url, last_updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (scheme_code) DO UPDATE SET
            title = EXCLUDED.title,
            summary_english = EXCLUDED.summary_english,
            summary_hindi = EXCLUDED.summary_hindi,
            benefits_json = EXCLUDED.benefits_json,
            eligibility_json = EXCLUDED.eligibility_json,
            required_docs_json = EXCLUDED.required_docs_json,
            official_portal_url = EXCLUDED.official_portal_url,
            last_updated_at = EXCLUDED.last_updated_at""",
        scheme_id, scheme_code, title, government_level, state_name, category,
        summary_eng, summary_hin, benefits_str, eligibility_str, docs_str, portal_url, now
    )

    return {"message": "Scheme ingested successfully", "scheme_code": scheme_code, "title": title}


@router.post("/match")
@limiter.limit("15/minute")
async def match_citizen_eligibility(
    request: Request,
    req: SchemeMatchRequest,
    db=Depends(get_db)
):
    """
    Evaluates citizen demographic profile against all active central & state
    schemes, returning a ranked match list with Match %, gap analysis, and official links.
    """
    await seed_default_schemes_if_empty(db)

    rows = await db.fetch("SELECT * FROM yojana_schemes")
    all_matches = []

    for r in rows:
        item = dict(r)
        try:
            item["benefits"] = json.loads(item.get("benefits_json") or "[]")
            item["eligibility"] = json.loads(item.get("eligibility_json") or "{}")
            item["required_docs"] = json.loads(item.get("required_docs_json") or "[]")
        except Exception:
            item["benefits"] = []
            item["eligibility"] = {}
            item["required_docs"] = []

        evaluation = evaluate_scheme_eligibility(item, req)
        all_matches.append(evaluation)

    # Sort by match_score DESC
    all_matches.sort(key=lambda x: (x["match_score"], x["scheme"]["title"]), reverse=True)

    eligible_count = sum(1 for m in all_matches if m["status"] == "eligible")
    partial_count = sum(1 for m in all_matches if m["status"] == "partial")

    return {
        "profile_summary": {
            "state": req.state,
            "occupation": req.occupation,
            "annual_income": req.annual_income,
            "category": req.category
        },
        "total_schemes_evaluated": len(all_matches),
        "eligible_count": eligible_count,
        "partial_count": partial_count,
        "matches": all_matches
    }


@router.get("/blogs")
async def list_ai_blogs(db=Depends(get_db)):
    """Fetch AI-generated citizen guides and scheme articles."""
    from services.yojana_blog_service import seed_default_blogs_if_empty
    await seed_default_blogs_if_empty(db)

    rows = await db.fetch("SELECT * FROM yojana_blogs ORDER BY published_at DESC")
    blogs = []
    for r in rows:
        item = dict(r)
        try:
            item["official_links"] = json.loads(item.get("official_links_json") or "[]")
        except Exception:
            item["official_links"] = []
        blogs.append(item)

    return {"count": len(blogs), "blogs": blogs}


@router.get("/blogs/{slug}")
async def get_blog_by_slug(slug: str, db=Depends(get_db)):
    """Fetch a single AI citizen guide by unique slug."""
    from services.yojana_blog_service import seed_default_blogs_if_empty
    await seed_default_blogs_if_empty(db)

    row = await db.fetchrow("SELECT * FROM yojana_blogs WHERE slug = $1", slug)
    if not row:
        raise HTTPException(status_code=404, detail="AI Citizen Guide not found.")

    item = dict(row)
    try:
        item["official_links"] = json.loads(item.get("official_links_json") or "[]")
    except Exception:
        item["official_links"] = []

    return {"blog": item}


