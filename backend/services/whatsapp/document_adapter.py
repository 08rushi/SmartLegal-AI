"""
document_adapter.py — WhatsApp Document Intake Adapter.

Translates downloaded WhatsApp media into SmartLegal AI's existing
document validation, storage, and database registration pipeline.
"""

import datetime
import logging
import os
import re
import uuid
from typing import Dict, Any

from routers.upload import _validate_file, _store_file
from services.whatsapp.media import DownloadedMedia

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal, unsafe characters, or injection attacks.
    """
    if not filename:
        return "document.pdf"

    # Strip path components and null bytes
    cleaned = os.path.basename(filename).replace("\x00", "")
    # Remove directory traversal sequences
    cleaned = re.sub(r"\.\.+[/\\]", "", cleaned)
    # Retain only safe alphanumeric, dash, underscore, dot characters
    safe_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)
    return safe_name.strip("._") or "document.pdf"


async def process_whatsapp_document_intake(
    db: Any,
    contact: Dict[str, Any],
    downloaded: DownloadedMedia,
    message_id: str,
) -> Dict[str, Any]:
    """
    Process incoming WhatsApp document media:
    1. Sanitize filename.
    2. Validate file content using existing SmartLegal security rules (_validate_file).
    3. Store file durably using existing storage pipeline (_store_file).
    4. Register document in the 'documents' DB table linked to the user/contact.
    5. Return registered document record dict.
    """
    safe_filename = sanitize_filename(downloaded.filename)
    user_id = contact.get("user_id") or contact["id"]

    # 1. Content-signature & Security Validation (Reuses existing SmartLegal rules)
    detected_mime = _validate_file(downloaded.content, safe_filename)

    # 2. File Storage (Reuses existing SmartLegal Cloudinary / local storage)
    file_url = _store_file(downloaded.content, safe_filename, user_id)

    # 3. Create Document DB Record
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if db is not None:
        await db.execute(
            """
            INSERT INTO documents (
                id, user_id, filename, file_url, file_size, document_type, status, uploaded_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            doc_id,
            user_id,
            safe_filename,
            file_url,
            downloaded.file_size,
            detected_mime,
            "ready",
            now_iso,
        )

        try:
            from services.whatsapp.context_repository import set_active_document
            await set_active_document(db, contact["id"], doc_id, workflow_state="document_received")
        except Exception as exc:
            logger.warning(f"[whatsapp-intake] Could not set active context: {exc}")

    logger.info(f"[whatsapp-intake] Document {doc_id} ('{safe_filename}') successfully registered for contact {contact['id']}.")

    return {
        "id": doc_id,
        "user_id": user_id,
        "filename": safe_filename,
        "file_url": file_url,
        "file_size": downloaded.file_size,
        "document_type": detected_mime,
        "status": "ready",
        "uploaded_at": now_iso,
    }
