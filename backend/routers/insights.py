"""
insights.py — on-demand AI insights derived from a document's stored analysis.

Two features:
  POST /insights/{document_id}/consequences  → "What happens if I sign?" simulation
  POST /insights/{document_id}/negotiation    → safer-clause rewrites + counter text

Both:
  - require auth + verify document ownership,
  - reuse the already-stored analysis (no PDF re-parsing, no extra classification),
  - cache the generated result in `document_insights` (upsert keyed by document_id+kind),
    so re-opening is instant and free. Pass ?force=true to regenerate.
"""

import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.groq_service import simulate_consequences, generate_negotiation
from services.lang import lang_from_request

router = APIRouter()
logger = logging.getLogger(__name__)


async def _load_owned_analysis(db, document_id: str, current_user: dict):
    """Return (document_row, analysis_dict) after verifying ownership + that analysis exists."""
    doc = await db.fetchrow("SELECT * FROM documents WHERE id = $1", document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to access this document.")

    row = await db.fetchrow(
        "SELECT result_json FROM analyses WHERE document_id = $1", document_id
    )
    if not row:
        raise HTTPException(status_code=400, detail="Please analyze this document first.")
    analysis = json.loads(row["result_json"])
    status = analysis.get("status")
    if (status not in (None, "done")) or not analysis.get("clauses"):
        raise HTTPException(status_code=400, detail="Please analyze this document first.")
    return doc, analysis


async def _get_cached(db, document_id: str, kind: str):
    row = await db.fetchrow(
        "SELECT result_json FROM document_insights WHERE document_id = $1 AND kind = $2",
        document_id, kind,
    )
    return json.loads(row["result_json"]) if row else None


async def _store(db, document_id: str, kind: str, data: dict) -> None:
    await db.execute(
        """INSERT INTO document_insights (id, document_id, kind, result_json, created_at)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (document_id, kind)
           DO UPDATE SET result_json = EXCLUDED.result_json, created_at = EXCLUDED.created_at""",
        str(uuid.uuid4()), document_id, kind, json.dumps(data), datetime.utcnow().isoformat(),
    )


def _kind(base: str, lang: str) -> str:
    """Cache key per language. English keeps the legacy key so existing cached rows still hit."""
    return base if lang == "en" else f"{base}:{lang}"


def _doc_type_of(doc, analysis) -> str:
    return (
        analysis.get("summary", {}).get("document_type")
        or (doc["document_type"] if doc["document_type"] else "")
        or "legal document"
    )


@router.post("/{document_id}/consequences")
@limiter.limit("10/minute")
async def get_consequences(
    request: Request,
    document_id: str,
    force: bool = False,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc, analysis = await _load_owned_analysis(db, document_id, current_user)
    lang = lang_from_request(request)
    kind = _kind("consequences", lang)

    if not force:
        cached = await _get_cached(db, document_id, kind)
        if cached:
            return {"consequences": cached, "cached": True, "lang": lang}

    try:
        data = await simulate_consequences(
            _doc_type_of(doc, analysis), analysis.get("summary", {}), analysis.get("clauses", []), lang=lang
        )
    except Exception as exc:
        logger.exception("[insights] consequences failed for %s: %s", document_id, type(exc).__name__)
        raise HTTPException(status_code=502, detail="Could not generate consequences right now. Please try again.")

    await _store(db, document_id, kind, data)
    return {"consequences": data, "cached": False, "lang": lang}


@router.post("/{document_id}/negotiation")
@limiter.limit("10/minute")
async def get_negotiation(
    request: Request,
    document_id: str,
    force: bool = False,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc, analysis = await _load_owned_analysis(db, document_id, current_user)
    lang = lang_from_request(request)
    kind = _kind("negotiation", lang)

    if not force:
        cached = await _get_cached(db, document_id, kind)
        if cached:
            return {"negotiation": cached, "cached": True, "lang": lang}

    try:
        data = await generate_negotiation(
            _doc_type_of(doc, analysis), analysis.get("summary", {}), analysis.get("clauses", []), lang=lang
        )
    except Exception as exc:
        logger.exception("[insights] negotiation failed for %s: %s", document_id, type(exc).__name__)
        raise HTTPException(status_code=502, detail="Could not generate negotiation guidance right now. Please try again.")

    await _store(db, document_id, kind, data)
    return {"negotiation": data, "cached": False, "lang": lang}
