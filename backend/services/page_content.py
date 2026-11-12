"""
page_content.py — Canonical PageContent Representation & Quality Scoring (Phase 2).

Defines:
  1. `PageContent`: Dataclass capturing per-page extraction provenance, observable
     telemetry, and derived readability/classification metrics.
  2. `PageContentList`: A list subclass providing backward-compatible string conversion
     and document-level classification properties.
  3. Deterministic quality scoring functions and routing classifiers.
  4. `pages_to_text`: Canonical reconstruction of the legacy `[Page N]` string contract.

Architectural Notice:
  `quality_score` is a deterministic readability and extraction-quality heuristic.
  It reflects character-level density and typographic coherence.
  It does NOT represent legal accuracy, semantic correctness, or OCR correctness.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import get_settings


def _is_letter(ch: str) -> bool:
    """
    Unicode-aware check for alphabetic letters and Indic combining vowel marks (matras).
    In Indic scripts (Devanagari, Tamil, Telugu, etc.), combining vowel signs belong to
    Unicode categories 'Mn' (Nonspacing Mark) or 'Mc' (Spacing Combining Mark).
    """
    if ch.isalpha():
        return True
    return unicodedata.category(ch) in ("Mn", "Mc")


# =============================================================================
# 1. Canonical PageContent Schema
# =============================================================================

@dataclass
class PageContent:
    """
    Normalized per-page representation of an extracted document page.

    Strictly isolates observed/extracted telemetry from derived classification fields.
    """

    # -------------------------------------------------------------------------
    # A. OBSERVED / EXTRACTED FIELDS (Gathered directly from document / engine)
    # -------------------------------------------------------------------------
    page_num: int
    """1-indexed physical page number within the document."""

    text: str
    """Extracted text string for this page with basic whitespace normalization."""

    extraction_source: str
    """Provenance engine: 'pymupdf' | 'tesseract'."""

    script: str
    """
    Dominant linguistic script detected on this page (e.g. 'Latin / English',
    'Hindi / Marathi (Devanagari)', 'Tamil', 'Telugu', 'Bengali / Assamese', etc.).
    """

    ocr_confidence: Optional[float] = None
    """
    Genuine word-level confidence reported directly by the OCR engine (scaled 0.0 to 1.0).
    STRICT CONTRACT: Must be None for digital PyMuPDF extractions, None when OCR was not
    executed, None when Tesseract produced no words or invalid confidences, and None on
    OCR error. NEVER 0.0 to represent 'unknown' or 'unavailable'.
    """

    char_count: int = 0
    """Length of extracted text (stripped)."""

    word_count: int = 0
    """Total words detected on page."""

    has_images: bool = False
    """True if one or more raster image streams exist on this page."""

    image_count: int = 0
    """Count of raster image streams detected on this page."""

    raw_signals: Dict[str, Any] = field(default_factory=dict)
    """
    Observable telemetry dictionary:
    {'alpha_count': int, 'non_space_count': int, 'letter_ratio': float, 'valid_ocr_word_count': int}
    """

    # -------------------------------------------------------------------------
    # B. DERIVED / CLASSIFICATION FIELDS (Computed deterministically)
    # -------------------------------------------------------------------------
    page_type: str = "digital"
    """
    Structural category of page content:
    - 'digital': Meaningful native vector text present (alpha_count >= DIGITAL_MIN_LETTERS
                 and letter_ratio >= DIGITAL_MIN_LETTER_RATIO).
    - 'scanned': Insufficient native vector text AND raster images detected.
    - 'empty':   Insufficient native vector text AND no raster images detected.
    """

    quality_score: float = 0.0
    """
    Deterministic extraction / readability quality heuristic in range [0.0, 1.0].
    DISCLAIMER: Reflects typographic coherence and character-density quality.
    Does NOT represent legal validity, factual accuracy, or OCR accuracy.
    """

    is_unclear: bool = False
    """
    Deterministic boolean triage indicator.
    - For digital pages: quality_score < PAGE_READABLE_QUALITY_THRESHOLD
    - For scanned/OCR pages: (quality_score < PAGE_READABLE_QUALITY_THRESHOLD)
      or (ocr_confidence is not None and ocr_confidence < OCR_MIN_CONFIDENCE_THRESHOLD)
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert page record to JSON-serializable dictionary."""
        return {
            "page_num": self.page_num,
            "text": self.text,
            "extraction_source": self.extraction_source,
            "script": self.script,
            "ocr_confidence": self.ocr_confidence,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "has_images": self.has_images,
            "image_count": self.image_count,
            "raw_signals": self.raw_signals,
            "page_type": self.page_type,
            "quality_score": self.quality_score,
            "is_unclear": self.is_unclear,
        }


# =============================================================================
# 2. PageContentList Container
# =============================================================================

class PageContentList(list):
    """
    A list subclass of PageContent objects providing backward-compatible
    string conversion and document-level classification properties.
    """

    def to_text(self) -> str:
        """Render all pages as a single string with [Page N] boundary markers."""
        return pages_to_text(self)

    @property
    def document_type(self) -> str:
        """
        Document-level classification:
        'digital_pdf' | 'scanned_pdf' | 'mixed_pdf' | 'empty_pdf'.
        """
        return classify_document_pages(self)

    def __str__(self) -> str:
        return self.to_text()


# =============================================================================
# 3. Deterministic Scoring & Classification Helpers
# =============================================================================

def calculate_digital_quality(
    text: str,
    settings: Any = None,
) -> tuple[float, bool, Dict[str, Any]]:
    """
    Calculate readability quality heuristic for a native digital text page.

    Observable inputs:
      - alpha_count: Number of Unicode alphabetic characters.
      - non_space_count: Number of non-whitespace characters.
      - letter_ratio: alpha_count / non_space_count.

    Returns:
      (quality_score, is_unclear, raw_signals)
    """
    s = settings or get_settings()
    min_letters = getattr(s, "digital_min_letters", 20)
    min_ratio = getattr(s, "digital_min_letter_ratio", 0.40)
    full_prose_ratio = getattr(s, "digital_full_prose_ratio", 0.90)
    length_scale_chars = getattr(s, "digital_length_scale_chars", 100)
    readable_threshold = getattr(s, "page_readable_quality_threshold", 0.40)

    stripped = text.strip()
    if not stripped:
        signals = {
            "alpha_count": 0,
            "non_space_count": 0,
            "letter_ratio": 0.0,
        }
        return 0.0, True, signals

    alpha_count = sum(1 for ch in stripped if _is_letter(ch))
    non_space_count = sum(1 for ch in stripped if not ch.isspace())
    letter_ratio = alpha_count / non_space_count if non_space_count > 0 else 0.0

    signals = {
        "alpha_count": alpha_count,
        "non_space_count": non_space_count,
        "letter_ratio": round(letter_ratio, 4),
    }

    if alpha_count < min_letters or letter_ratio < min_ratio:
        # Insufficient letters or low letter-ratio (e.g. garbled symbols or isolated numbers)
        quality_score = round(min(0.39, letter_ratio * 0.5), 3)
    else:
        # Scale from 0.50 at boundary up to 1.0 for clean prose
        ratio_span = max(0.01, full_prose_ratio - min_ratio)
        base_score = min(
            1.0,
            0.50 + ((letter_ratio - min_ratio) / ratio_span) * 0.50,
        )
        length_scale = min(1.0, alpha_count / float(length_scale_chars))
        quality_score = round(max(0.40, min(1.0, base_score * length_scale)), 3)

    is_unclear = quality_score < readable_threshold
    return quality_score, is_unclear, signals


def calculate_ocr_quality(
    ocr_confidence: Optional[float],
    text: str,
    settings: Any = None,
) -> tuple[float, bool, Dict[str, Any]]:
    """
    Calculate readability quality heuristic for a page extracted via OCR.

    Observable inputs:
      - ocr_confidence: Genuine average word confidence from OCR engine, or None.
      - text: Extracted text string.

    Returns:
      (quality_score, is_unclear, raw_signals)
    """
    s = settings or get_settings()
    readable_threshold = getattr(s, "page_readable_quality_threshold", 0.40)
    min_ocr_conf = getattr(s, "ocr_min_confidence_threshold", 0.35)

    stripped = text.strip()
    alpha_count = sum(1 for ch in stripped if _is_letter(ch))
    non_space_count = sum(1 for ch in stripped if not ch.isspace())
    letter_ratio = alpha_count / non_space_count if non_space_count > 0 else 0.0

    signals = {
        "alpha_count": alpha_count,
        "non_space_count": non_space_count,
        "letter_ratio": round(letter_ratio, 4),
        "ocr_confidence": ocr_confidence,
    }

    if ocr_confidence is not None:
        # 70% weighted on OCR engine confidence, 30% weighted on typographic letter-ratio
        quality_score = round(
            0.70 * ocr_confidence + 0.30 * min(1.0, letter_ratio / 0.75),
            3,
        )
        is_unclear = (
            quality_score < readable_threshold
            or ocr_confidence < min_ocr_conf
        )
    else:
        # OCR produced no words or failed
        quality_score = 0.0
        is_unclear = True

    return quality_score, is_unclear, signals


def classify_page(
    alpha_count: int,
    letter_ratio: float,
    has_images: bool,
    settings: Any = None,
) -> str:
    """
    Determine the structural page format using strictly deterministic signals:
      - 'digital': Meaningful native vector text present.
      - 'scanned': Insufficient native text AND raster images detected.
      - 'empty':   Insufficient native text AND no raster images detected.
    """
    s = settings or get_settings()
    min_letters = getattr(s, "digital_min_letters", 20)
    min_ratio = getattr(s, "digital_min_letter_ratio", 0.40)

    if alpha_count >= min_letters and letter_ratio >= min_ratio:
        # If the page has raster images and minimal text (< 100 letters),
        # it is predominantly a scanned page with only a stamp/header.
        if has_images and alpha_count < 100:
            return "scanned"
        return "digital"
    elif has_images:
        return "scanned"
    else:
        return "empty"


def classify_document_pages(pages: List[PageContent]) -> str:
    """
    Determine document-level route classification from page list:
      - 'digital_pdf': All non-empty pages are 'digital'.
      - 'scanned_pdf': All non-empty pages are 'scanned'.
      - 'mixed_pdf': Document contains BOTH 'digital' and 'scanned' pages.
      - 'empty_pdf': All pages are 'empty' (or document has zero pages).
    """
    if not pages:
        return "empty_pdf"

    non_empty = [p for p in pages if p.page_type != "empty"]
    if not non_empty:
        return "empty_pdf"

    types = {p.page_type for p in non_empty}
    if types == {"digital"}:
        return "digital_pdf"
    elif types == {"scanned"}:
        return "scanned_pdf"
    elif "digital" in types and "scanned" in types:
        return "mixed_pdf"
    else:
        return "digital_pdf"


def pages_to_text(pages: List[PageContent]) -> str:
    """
    Reconstruct canonical plain text with [Page N] headers, matching the
    exact format consumed by groq_service, detect_document_type, and Redis cache.
    """
    pages_text: list[str] = []
    for page in pages:
        body = page.text.strip()
        if body:
            pages_text.append(f"[Page {page.page_num}]\n{body}")

    full_text = "\n\n".join(pages_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    return "\n".join(line for line in full_text.splitlines() if line.strip())
