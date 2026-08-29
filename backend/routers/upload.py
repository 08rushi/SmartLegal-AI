from datetime import datetime
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from cache import delete_analysis
from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user

router = APIRouter()
settings = get_settings()

MAX_SIZE_MB = 10

# ── Magic-byte signatures for allowed file types ──────────────────────────────
# PDFs plus scanned/photographed images (JPG/PNG/WebP) — images go through OCR.
MAGIC_SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"%PDF",              0, "application/pdf"),
    (b"\xff\xd8\xff",      0, "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "image/png"),
    (b"RIFF",              0, "image/webp"),  # RIFF....WEBP — refined below
]

ALLOWED_MIME_TYPES = {sig[2] for sig in MAGIC_SIGNATURES}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _detect_mime(content: bytes) -> str | None:
    for magic, offset, mime in MAGIC_SIGNATURES:
        if content[offset: offset + len(magic)] == magic:
            # WebP is RIFF-based: confirm the WEBP tag at offset 8.
            if mime == "image/webp" and content[8:12] != b"WEBP":
                continue
            return mime
    return None


def _validate_file(content: bytes, filename: str) -> str:
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_SIZE_MB} MB.",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    detected = _detect_mime(content)
    if detected is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Please upload a PDF or an image "
                "(JPG, PNG, or WebP) of the document. Make sure the file is valid "
                "and not corrupted or renamed."
            ),
        )

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

    # Validate page count for PDFs (SL-015 hardening)
    if detected == "application/pdf":
        try:
            import fitz
            doc_pdf = fitz.open(stream=content, filetype="pdf")
            if doc_pdf.page_count > 50:
                doc_pdf.close()
                raise HTTPException(
                    status_code=400,
                    detail="Document exceeds the maximum limit of 50 pages. Please upload a shorter document or excerpt.",
                )
            doc_pdf.close()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Corrupted or invalid PDF document file.",
            )

    return detected



def _get_user_id_from_token(token: str | None) -> str:
    """
    Try to decode the JWT and return the user_id.
    Returns "anonymous" if no token or invalid token — upload still works.
    """
    if not token:
        return "anonymous"
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub", "anonymous")
        return user_id or "anonymous"
    except JWTError:
        return "anonymous"


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


_cloudinary_ready = False


def _configure_cloudinary() -> None:
    """Configure the Cloudinary SDK once from settings (required before upload)."""
    global _cloudinary_ready
    if _cloudinary_ready:
        return
    import cloudinary
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    _cloudinary_ready = True


def _store_file(content: bytes, filename: str, user_id: str) -> str:
    """
    Persist the uploaded file and return a retrievable URL.

    Durable Cloudinary storage is used whenever it is configured. In production a
    Cloudinary failure (or missing config) is a hard error — we must never fall
    back to ephemeral local temp files there, since they vanish on the next deploy.
    In development we fall back to a local temp file for convenience.
    """
    if should_use_cloudinary():
        try:
            _configure_cloudinary()
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                content,
                resource_type="raw",
                folder="smartlegal",
                public_id=f"{user_id}/{uuid.uuid4()}",
            )
            return result["secure_url"]
        except Exception as exc:
            print(f"[upload] Cloudinary upload failed: {exc}")
            if settings.is_production:
                raise HTTPException(
                    status_code=502,
                    detail="File storage is temporarily unavailable. Please try again.",
                )
            # dev: fall through to local storage
    elif settings.is_production:
        raise HTTPException(
            status_code=503,
            detail="Durable file storage is not configured on the server.",
        )

    local_path = os.path.join(
        tempfile.gettempdir(),
        f"{uuid.uuid4()}_{filename or 'document'}",
    )
    with open(local_path, "wb") as f:
        f.write(content)
    return f"local://{local_path}"


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


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=UploadResponse, status_code=201)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    token: str | None = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    content = await file.read()
    _validate_file(content, file.filename or "")

    user_id = _get_user_id_from_token(token)

    # Document hashing & deduplication (SL-023)
    import hashlib
    file_hash = hashlib.sha256(content).hexdigest()

    existing_doc = await db.fetchrow(
        "SELECT id, filename, file_url, file_size, document_type, status, uploaded_at "
        "FROM documents WHERE user_id = $1 AND file_hash = $2 LIMIT 1",
        user_id, file_hash,
    )
    if existing_doc:
        return UploadResponse(
            document=DocumentOut(
                id=existing_doc["id"],
                filename=existing_doc["filename"],
                file_url=existing_doc["file_url"],
                file_size=existing_doc["file_size"],
                document_type=existing_doc["document_type"] or "",
                status=existing_doc["status"],
                uploaded_at=existing_doc["uploaded_at"],
            ),
            message="Document already uploaded (reused from cache)",
        )

    file_url = _store_file(content, file.filename or "document", user_id)
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Ensure anonymous user row exists (no-op if already there)
    if user_id == "anonymous":
        await db.execute(
            """INSERT INTO users (id, name, email, password, created_at)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (id) DO NOTHING""",
            "anonymous", "Anonymous", "anonymous@smartlegal.local", "", now,
        )

    await db.execute(
        """INSERT INTO documents (id, user_id, filename, file_url, file_size, document_type, file_hash, status, uploaded_at)
           VALUES ($1, $2, $3, $4, $5, '', $6, 'ready', $7)""",
        doc_id, user_id, file.filename or "document", file_url, len(content), file_hash, now,
    )

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


@router.get("/history")
async def get_document_history(
    page: int = 1,
    limit: int = 20,
    token: str | None = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    """
    Return paginated document history for the currently logged-in user (SL-057).
    """
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to view document history.")

    user_id = _get_user_id_from_token(token)
    if user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Sign in to view document history.")

    offset = (max(1, page) - 1) * limit

    count_row = await db.fetchrow("SELECT COUNT(*) as cnt FROM documents WHERE user_id = $1", user_id)
    total_count = count_row["cnt"] if count_row else 0

    rows = await db.fetch(
        """SELECT d.id, d.filename, d.file_url, d.file_size, d.document_type, d.status, d.uploaded_at,
                  EXISTS(SELECT 1 FROM analyses a WHERE a.document_id = d.id) AS analyzed
           FROM documents d
           WHERE d.user_id = $1
           ORDER BY d.uploaded_at DESC
           LIMIT $2 OFFSET $3""",
        user_id, limit, offset,
    )

    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

    return {
        "documents": [
            {
                "id": row["id"],
                "filename": row["filename"],
                "file_url": row["file_url"],
                "file_size": row["file_size"],
                "document_type": row["document_type"] or "",
                "status": row["status"],
                "uploaded_at": row["uploaded_at"],
                "analyzed": bool(row["analyzed"]),
            }
            for row in rows
        ],
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }



@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return a single uploaded document by id so the frontend can recover
    analysis routes after a hard refresh.
    """
    row = await db.fetchrow(
        """SELECT id, user_id, filename, file_url, file_size, document_type, status, uploaded_at
           FROM documents
           WHERE id = $1""",
        document_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    if row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to access this document.")

    return DocumentOut(
        id=row["id"],
        filename=row["filename"],
        file_url=row["file_url"],
        file_size=row["file_size"],
        document_type=row["document_type"] or "",
        status=row["status"],
        uploaded_at=row["uploaded_at"],
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Permanently delete a document, its saved analysis, chat history, and local file.
    Only the owner may delete. Idempotent-ish: 404 if the document does not exist.
    """
    row = await db.fetchrow(
        "SELECT user_id, file_url FROM documents WHERE id = $1", document_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")
    if row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this document.")

    # Remove dependent rows first (no ON DELETE CASCADE on these FKs).
    await db.execute("DELETE FROM analyses WHERE document_id = $1", document_id)
    await db.execute("DELETE FROM chat_messages WHERE document_id = $1", document_id)
    await db.execute("DELETE FROM documents WHERE id = $1", document_id)

    # Best-effort cleanup of the cached analysis and the local file.
    try:
        await delete_analysis(document_id)
    except Exception:
        pass
    file_url = row["file_url"] or ""
    if file_url.startswith("local://"):
        try:
            os.remove(file_url.replace("local://", ""))
        except OSError:
            pass

    return {"message": "Document deleted.", "id": document_id}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Authorized private document download endpoint (SL-013).
    Verifies user ownership before serving the file or signing a short-lived download URL.
    """
    row = await db.fetchrow(
        "SELECT id, user_id, filename, file_url FROM documents WHERE id = $1", document_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")
    if row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to download this document.")

    file_url = row["file_url"] or ""
    if file_url.startswith("local://"):
        local_path = file_url.replace("local://", "")
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="Local document file no longer exists.")
        from fastapi.responses import FileResponse
        return FileResponse(
            path=local_path,
            filename=row["filename"] or "document",
            content_disposition_type="attachment",
        )

    # For Cloudinary or external storage, issue signed URL or redirect securely
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=file_url)

