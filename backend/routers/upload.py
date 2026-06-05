from datetime import datetime
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config import get_settings
from database import get_db
from limiter import limiter
from routers.auth import get_current_user

router = APIRouter()
settings = get_settings()

MAX_SIZE_MB = 10

# ── Magic-byte signatures for allowed file types ──────────────────────────────
MAGIC_SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"%PDF",          0, "application/pdf"),
]

ALLOWED_MIME_TYPES = {sig[2] for sig in MAGIC_SIGNATURES}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _detect_mime(content: bytes) -> str | None:
    for magic, offset, mime in MAGIC_SIGNATURES:
        if content[offset: offset + len(magic)] == magic:
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
                "Unsupported file type. Only PDF files are accepted. "
                "Make sure the file is a valid PDF and not corrupted or renamed."
            ),
        )

    declared_ext = os.path.splitext(filename or "")[1].lower()
    ext_to_mime = {
        ".pdf":  "application/pdf",
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

    # Use logged-in user if token present, otherwise anonymous
    user_id = _get_user_id_from_token(token)

    file_url = ""
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
        local_path = os.path.join(
            tempfile.gettempdir(),
            f"{uuid.uuid4()}_{file.filename or 'document'}",
        )
        with open(local_path, "wb") as f:
            f.write(content)
        file_url = f"local://{local_path}"

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Ensure anonymous user row exists (no-op if already there)
    if user_id == "anonymous":
        await db.execute(
            """INSERT OR IGNORE INTO users (id, name, email, password, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("anonymous", "Anonymous", "anonymous@smartlegal.local", "", now),
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


@router.get("/history")
async def get_document_history(
    token: str | None = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    """
    Return all documents for the currently logged-in user.
    Requires a valid JWT — returns 401 if not authenticated.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to view document history.")

    user_id = _get_user_id_from_token(token)
    if user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Sign in to view document history.")

    async with db.execute(
        """SELECT id, filename, file_url, file_size, document_type, status, uploaded_at
           FROM documents
           WHERE user_id = ?
           ORDER BY uploaded_at DESC""",
        (user_id,),
    ) as cur:
        rows = await cur.fetchall()

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
            }
            for row in rows
        ]
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
    async with db.execute(
        """SELECT id, user_id, filename, file_url, file_size, document_type, status, uploaded_at
           FROM documents
           WHERE id = ?""",
        (document_id,),
    ) as cur:
        row = await cur.fetchone()

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
