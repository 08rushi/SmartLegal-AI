from fastapi import APIRouter, Depends, HTTPException
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


@router.post("")
async def analyze_document(
    req: AnalyzeRequest,
    db=Depends(get_db),
):
    # Check if analysis already exists (cache it)
    async with db.execute(
        "SELECT result_json FROM analyses WHERE document_id = ?", (req.document_id,)
    ) as cur:
        existing = await cur.fetchone()
    if existing:
        return {"analysis": json.loads(existing["result_json"])}

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
        raise HTTPException(status_code=400, detail="Could not extract text from document")

    # Run Gemini analysis
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
        "INSERT INTO analyses (id, document_id, result_json, analyzed_at) VALUES (?, ?, ?, ?)",
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
