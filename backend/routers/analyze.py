from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

from database import get_db
from services.gemini_service import analyze_legal_document
from services.pdf_parser import extract_text_from_pdf

router = APIRouter()


class AnalyzeRequest(BaseModel):
    document_id: str
    force_reanalyze: bool = False  # set to true to bypass cache


@router.post("")
async def analyze_document(
    req: AnalyzeRequest,
    db=Depends(get_db),
):
    # Check cache (unless force_reanalyze is requested)
    if not req.force_reanalyze:
        async with db.execute(
            "SELECT result_json FROM analyses WHERE document_id = ?", (req.document_id,)
        ) as cur:
            existing = await cur.fetchone()
        if existing:
            cached = json.loads(existing["result_json"])
            summary = cached.get("summary", {})
            cached_clause_count = len(cached.get("clauses", []))
            total_clauses = summary.get("total_clauses", 0)
            # Only use cache if it has actual extracted clauses.
            # Empty-clause summaries are often model failures and should be re-analyzed.
            if cached_clause_count > 0 or total_clauses > 0:
                return {"analysis": cached}
            # Otherwise fall through to re-analyze

    # Delete stale cache entry if exists
    await db.execute("DELETE FROM analyses WHERE document_id = ?", (req.document_id,))
    await db.commit()

    # Fetch document
    async with db.execute(
        "SELECT * FROM documents WHERE id = ?",
        (req.document_id,),
    ) as cur:
        doc = await cur.fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Extract text from PDF
    file_url = doc["file_url"]
    try:
        if file_url.startswith("local://"):
            local_path = file_url.replace("local://", "")
            with open(local_path, "rb") as f:
                file_bytes = f.read()
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url)
                file_bytes = resp.content

        text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read document: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from document. Make sure it's a text-based PDF (not a scanned image).")

    print(f"[analyze] Extracted {len(text)} characters from {doc['filename']}")

    # Run AI analysis
    try:
        analysis = await analyze_legal_document(text, doc["filename"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    # Add metadata
    analysis["document_id"] = req.document_id
    analysis["analyzed_at"] = datetime.utcnow().isoformat()

    # Cache result
    analysis_id = str(uuid.uuid4())
    await db.execute(
        "INSERT OR REPLACE INTO analyses (id, document_id, result_json, analyzed_at) VALUES (?, ?, ?, ?)",
        (analysis_id, req.document_id, json.dumps(analysis), analysis["analyzed_at"]),
    )

    # Update document type in DB
    doc_type = analysis.get("summary", {}).get("document_type", "")
    await db.execute(
        "UPDATE documents SET document_type = ? WHERE id = ?",
        (doc_type, req.document_id),
    )

    await db.commit()
    return {"analysis": analysis}


@router.delete("/{document_id}/cache")
async def clear_analysis_cache(document_id: str, db=Depends(get_db)):
    """Clear cached analysis so document gets re-analyzed fresh."""
    await db.execute("DELETE FROM analyses WHERE document_id = ?", (document_id,))
    await db.commit()
    return {"message": "Cache cleared"}
