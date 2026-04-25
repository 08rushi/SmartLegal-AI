from datetime import datetime
import mimetypes
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from config import get_settings
from database import get_db

router = APIRouter()
settings = get_settings()

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 10


def should_use_cloudinary() -> bool:
    values = [
        settings.cloudinary_cloud_name,
        settings.cloudinary_api_key,
        settings.cloudinary_api_secret,
    ]
    return all(
        value and not value.strip().lower().startswith("your_")
        for value in values
    )


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_url: str
    file_size: int
    document_type: str
    status: str
    uploaded_at: str


class UploadResponse(BaseModel):
    document: DocumentOut
    message: str


@router.post("", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]

    # Validate file type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Please upload a PDF or image."
        )

    # Read file content
    content = await file.read()

    # Validate file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_SIZE_MB}MB."
        )

    # Try to upload to Cloudinary; fall back to local storage for dev
    file_url = ""
    user_id = "anonymous"
    if should_use_cloudinary():
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                content,
                resource_type="raw",
                folder="smartlegal",
                public_id=f"{user_id}/{uuid.uuid4()}",
            )
            file_url = result["secure_url"]
        except Exception:
            file_url = ""

    if not file_url:
        # Dev fallback: store file locally
        local_path = os.path.join(
            tempfile.gettempdir(),
            f"{uuid.uuid4()}_{file.filename or 'document'}",
        )
        with open(local_path, "wb") as f:
            f.write(content)
        file_url = f"local://{local_path}"

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    await db.execute(
        """INSERT OR IGNORE INTO users (id, name, email, password, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, "Anonymous", "anonymous@smartlegal.local", "", now),
    )
    await db.execute(
        """INSERT INTO documents (id, user_id, filename, file_url, file_size, status, uploaded_at)
           VALUES (?, ?, ?, ?, ?, 'ready', ?)""",
        (doc_id, user_id, file.filename or "document", file_url, len(content), now),
    )
    await db.commit()

    return UploadResponse(
        document=DocumentOut(
            id=doc_id,
            filename=file.filename or "document",
            file_url=file_url,
            file_size=len(content),
            document_type="",
            status="ready",
            uploaded_at=now,
        ),
        message="Document uploaded successfully",
    )
