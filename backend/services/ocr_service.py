"""
ocr_service.py — OCR for scanned / photographed legal documents (images + image-only PDFs).

Engine: Tesseract (via pytesseract). Free, offline, and the best free coverage for
Indian languages (Devanagari/Hindi/Marathi, Telugu, Tamil, Bengali, Gujarati, Kannada,
Malayalam, Punjabi, Odia, Urdu, …).

Design:
- Everything degrades gracefully. If Tesseract (the binary) or pytesseract (the python
  package) is not installed, `ocr_available()` returns False and the caller shows a clear
  setup message instead of crashing.
- Only languages actually installed as tessdata are requested, so a missing language pack
  never errors — we fall back to whatever is available (at least English).
- PDF pages are rasterised with PyMuPDF (already a dependency) — no Poppler/pdf2image needed.
"""

import io
import logging
from functools import lru_cache

import fitz  # PyMuPDF — already used by pdf_parser

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Preferred languages to try, in priority order. Intersected with what's installed.
_PREFERRED_LANGS = [
    "eng", "hin", "mar", "tel", "tam", "ben",
    "guj", "kan", "mal", "pan", "ori", "urd", "asm",
]

# Common Windows install location if tesseract isn't on PATH.
_WINDOWS_DEFAULTS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


@lru_cache(maxsize=1)
def _resolve() -> tuple[object, str]:
    """Return (pytesseract_module_or_None, reason). Cached — probing is cheap but not free."""
    try:
        import pytesseract  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - import guard
        return None, f"pytesseract not installed ({exc})"

    # Locate the tesseract binary: explicit config → PATH → known Windows paths.
    import shutil
    import os

    cmd = (settings.tesseract_cmd or "").strip()
    if not cmd:
        cmd = shutil.which("tesseract") or ""
    if not cmd:
        for candidate in _WINDOWS_DEFAULTS:
            if os.path.exists(candidate):
                cmd = candidate
                break
    if not cmd:
        return None, "Tesseract engine binary not found (install it or set TESSERACT_CMD)."

    pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        return None, f"Tesseract binary at '{cmd}' is not runnable ({exc})."
    return pytesseract, "ok"


def ocr_available() -> bool:
    if not settings.ocr_enabled:
        return False
    module, _ = _resolve()
    return module is not None


def ocr_status() -> dict:
    module, reason = _resolve()
    return {
        "enabled": settings.ocr_enabled,
        "available": module is not None and settings.ocr_enabled,
        "reason": reason,
        "languages": sorted(_installed_langs()) if module else [],
    }


@lru_cache(maxsize=1)
def _installed_langs() -> frozenset:
    module, _ = _resolve()
    if module is None:
        return frozenset()
    try:
        return frozenset(module.get_languages(config=""))
    except Exception:
        return frozenset({"eng"})


def _lang_string() -> str:
    """Build a tesseract `-l` string from configured/preferred langs that are installed."""
    installed = _installed_langs()
    if not installed:
        return "eng"
    # Start from the operator-configured list, else the preferred defaults.
    configured = [l.strip() for l in (settings.ocr_languages or "").replace(",", "+").split("+") if l.strip()]
    wanted = configured or _PREFERRED_LANGS
    chosen = [l for l in wanted if l in installed]
    if not chosen:
        chosen = ["eng"] if "eng" in installed else [sorted(installed)[0]]
    return "+".join(dict.fromkeys(chosen))  # dedupe, keep order


def ocr_image_bytes(image_bytes: bytes) -> str:
    """OCR a single image (JPG/PNG/WebP). Returns extracted text (may be empty)."""
    module, reason = _resolve()
    if module is None:
        raise RuntimeError(reason)
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("L", "RGB"):
        img = img.convert("RGB")
    text = module.image_to_string(img, lang=_lang_string())
    return (text or "").strip()


def ocr_pdf_scanned(file_bytes: bytes, max_pages: int | None = None) -> str:
    """
    Rasterise each PDF page and OCR it. Used when a PDF has no usable text layer
    (a scan or photo saved as PDF). Returns text with [Page N] markers.
    """
    module, reason = _resolve()
    if module is None:
        raise RuntimeError(reason)
    from PIL import Image

    cap = max_pages or settings.ocr_max_pages
    lang = _lang_string()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text: list[str] = []
    try:
        for page_num in range(min(len(doc), cap)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)  # 300 DPI is the sweet spot for OCR accuracy
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
            text = (module.image_to_string(img, lang=lang) or "").strip()
            if text:
                pages_text.append(f"[Page {page_num + 1}]\n{text}")
    finally:
        doc.close()
    return "\n\n".join(pages_text).strip()
