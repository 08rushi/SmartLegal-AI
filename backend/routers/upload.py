from datetime import datetime
import mimetypes
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from config import get_settings
from database import get_db
from limiter import limiter

router = APIRouter()
settings = get_settings()

MAX_SIZE_MB = 10

# ── Magic-byte signatures for allowed file types ──────────────────────────────
# Each entry: (magic_bytes, offset, mime_type)
# We check the raw bytes so a renamed .exe can't sneak through.
MAGIC_SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"%PDF",       0, "application/pdf"),   # PDF
    (b"\xff\xd8\xff", 0, "image/jpeg"),       # JPEG
    (b"\x89PNG\r\n\x1a\n", 0, "image/png"),  # PNG
    (b"RIFF",       0, "image/webp"),         # WebP (RIFF container)
]

ALLOWED_MIME_TYPES = {sig[2] for sig in MAGIC_SIGNATURES}


def _detect_mime(content: bytes) -> str | None:
    """Return the detected MIME type from magic bytes, or None if unknown."""
    for magic, offset, mime in MAGIC_SIGNATURES:
        if content[offset: offset + len(magic)] == magic:
            # Extra WebP check: bytes 8-12 must be b"WEBP"
            if mime == "image/webp" and content[8:12] != b"WEBP":
                continue
            return mime
    return None


def _validate_file(content: bytes, filename: str) -> str:
    """
    Validate file content and return the detected MIME type.
    Raises HTTPException on any validation failure.
    """
    # 1. Size check (done after read so we have the bytes)
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_SIZE_MB} MB.",
        )

    # 2. Empty file check
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 3. Magic-byte detection (actual content, not just the extension/MIME header)
    detected = _detect_mime(content)
    if detected is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Only PDF, JPEG, PNG, and WebP are accepted. "
                "Make sure the file is not corrupted or renamed."
            ),
        )

    # 4. Sanity-check the declared extension matches what we detected
    declared_ext = os.path.splitext(filename or "")[1].lower()
    ext_to_mime = {
        ".pdf":  "application/pdf",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
    }
    expected_mime = ext_to_mime.get(declared_ext)
    if expected_mime and expected_mime != detected:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File extension '{declared_ext}' does not match the actual file content "
                f"(detected: {detected}). Please upload the correct file."
            ),
        )

    return detected


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


# ── Schemas ───────────────────────────────────────────────────────────────────

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


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=UploadResponse, status_code=201)
@limiter.limit("10/minute")          # max 10 uploads per IP per minute
async def upload_document(
    request: Request,                # required by slowapi
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    # Read file into memory (we need the bytes for magic-byte validation)
    content = await file.read()

    # Validate content (raises HTTPException on failure)
    _validate_file(content, file.filename or "")

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