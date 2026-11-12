"""
page_transcription.py — PageTranscription Contract (Phase 4 Visual / OCR Pipeline).

Defines the dedicated data representation for visual and optical transcription of document
pages, strictly decoupling visual understanding from downstream legal reasoning.

Key Design Principles:
  1. Separation of Concerns: Represents what is visually/textually present on the page,
     never legal conclusions, risk ratings, or clause classifications.
  2. Ground-Truth Provenance: Preserves exact extraction source ('pymupdf', 'gemini_vision',
     'paddleocr', 'tesseract') and engine version.
  3. Informational Confidence: Retains genuine OCR/Vision confidence as non-calibrated
     informational telemetry; never fabricates confidence.
  4. Uncertainty Markers: Supports genuine [UNCLEAR] markers without arbitrary loss of text.
  5. Downstream Interoperability: Directly converts to canonical PageContent via .to_page_content()
     for token-aware chunking (Phase 3) and downstream analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.page_content import PageContent


@dataclass
class PageTranscription:
    """
    Dedicated representation of visual transcription for an individual document page.
    """

    page_num: int
    """1-indexed physical page number."""

    text: str
    """Transcribed text content with layout/whitespace preserved."""

    extraction_source: str
    """
    Engine provenance:
    'pymupdf' | 'gemini_vision' | 'paddleocr' | 'tesseract'
    """

    engine: str
    """
    Concrete engine/model identifier, e.g.:
    'pymupdf', 'gemini-3.8-flash', 'paddleocr-v4', 'tesseract-5.x'
    """

    script: str = "Latin / English"
    """Dominant linguistic script detected on this page."""

    confidence: Optional[float] = None
    """
    Genuine word/character-level confidence reported directly by the vision/OCR engine (0.0 to 1.0).
    Strictly None if unmeasured or unavailable. Never fabricated.
    """

    is_unclear: bool = False
    """
    True if the transcribed text is genuinely degraded, contains [UNCLEAR] markers,
    or falls below the readable quality threshold.
    """

    quality_score: float = 0.0
    """Deterministic extraction / readability quality heuristic in range [0.0, 1.0]."""

    status: str = "success"
    """
    Execution lifecycle status:
    - 'success': Primary or chosen visual method transcribed successfully.
    - 'success_with_uncertainty': Transcribed successfully but contains [UNCLEAR] markers or marginal quality.
    - 'fallback_used': Primary method failed or low-quality, acceptable fallback succeeded.
    - 'provider_unavailable': Requested provider was disabled, misconfigured, or unreachable.
    - 'all_visual_methods_failed': All attempted visual/OCR methods failed on this page.
    """

    char_count: int = 0
    """Total character count of the transcribed text."""

    word_count: int = 0
    """Total word count of the transcribed text."""

    has_images: bool = False
    """True if visual raster streams exist on this page."""

    image_count: int = 0
    """Number of embedded image streams detected."""

    raw_signals: Dict[str, Any] = field(default_factory=dict)
    """Measurable telemetry dictionary (alpha_count, letter_ratio, gemini_confidence, etc.)."""

    fallback_history: List[Dict[str, Any]] = field(default_factory=list)
    """
    Auditable chronological attempt chain for this page:
    e.g. [
      {"engine": "gemini_vision", "status": "failed", "error_type": "rate_limit", "message": "429"},
      {"engine": "paddleocr", "status": "failed", "error_type": "low_quality", "signals": {...}},
      {"engine": "tesseract", "status": "success", "confidence": 0.82}
    ]
    """

    warnings: List[str] = field(default_factory=list)
    """Diagnostic warnings or error annotations collected during processing."""

    def __post_init__(self) -> None:
        if not self.char_count and self.text:
            self.char_count = len(self.text)
        if not self.word_count and self.text:
            self.word_count = len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard JSON-serializable dictionary."""
        return {
            "page_num": self.page_num,
            "text": self.text,
            "extraction_source": self.extraction_source,
            "engine": self.engine,
            "script": self.script,
            "confidence": self.confidence,
            "is_unclear": self.is_unclear,
            "quality_score": self.quality_score,
            "status": self.status,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "has_images": self.has_images,
            "image_count": self.image_count,
            "raw_signals": self.raw_signals,
            "fallback_history": self.fallback_history,
            "warnings": self.warnings,
        }

    def to_page_content(self) -> PageContent:
        """
        Convert to canonical PageContent representation for downstream Phase 3 chunking
        and Phase 1 analysis, preserving exact source provenance.
        """
        # Determine derived page_type
        if self.extraction_source == "pymupdf":
            p_type = "digital" if self.text.strip() else "empty"
        else:
            p_type = "scanned"

        return PageContent(
            page_num=self.page_num,
            text=self.text,
            extraction_source=self.extraction_source,
            script=self.script,
            ocr_confidence=self.confidence,
            char_count=self.char_count,
            word_count=self.word_count,
            has_images=self.has_images,
            image_count=self.image_count,
            raw_signals=self.raw_signals,
            page_type=p_type,
            quality_score=self.quality_score,
            is_unclear=self.is_unclear,
        )
