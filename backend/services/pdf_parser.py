"""
PDF text extraction using PyMuPDF (fitz).
Preserves page numbers and positions for accurate clause references.
"""

import fitz  # PyMuPDF
import re
from typing import List

from services.page_content import (
    PageContent,
    PageContentList,
    calculate_digital_quality,
    classify_page,
    classify_document_pages,
    pages_to_text,
)


def extract_text_from_pdf(file_bytes: bytes) -> PageContentList:
    """
    Extract per-page text and metadata from a PDF file using PyMuPDF.

    Returns:
        PageContentList: A list of PageContent instances with full telemetry,
        deterministic classification, and .to_text() / .document_type properties.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = PageContentList()

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            raw_text = page.get_text("text") or ""
            text = raw_text.replace("\xa0", " ").strip()

            # Inspect embedded raster image streams
            images = page.get_images(full=True)
            has_images = len(images) > 0
            image_count = len(images)

            # Linguistic script detection (preserves Indic and Latin scripts)
            script = detect_script(text)

            # Deterministic digital quality & signal computation
            quality_score, is_unclear, signals = calculate_digital_quality(text)

            # Structural page classification based purely on measurable signals:
            # - Meaningful native text: alpha_count >= 20 and letter_ratio >= 0.40 -> 'digital'
            # - Insufficient text and has raster images -> 'scanned'
            # - Insufficient text and no raster images -> 'empty'
            page_type = classify_page(
                alpha_count=signals["alpha_count"],
                letter_ratio=signals["letter_ratio"],
                has_images=has_images,
            )

            # For empty or scanned pages without text, ensure quality_score reflects no text
            if page_type == "empty":
                quality_score = 0.0
                is_unclear = True
            elif page_type == "scanned" and not text:
                quality_score = 0.0
                is_unclear = True

            word_count = len(text.split()) if text else 0

            pages.append(
                PageContent(
                    page_num=page_num + 1,
                    text=text,
                    extraction_source="pymupdf",
                    script=script,
                    ocr_confidence=None,  # Strictly None for PyMuPDF digital pages
                    char_count=len(text),
                    word_count=word_count,
                    has_images=has_images,
                    image_count=image_count,
                    raw_signals=signals,
                    page_type=page_type,
                    quality_score=quality_score,
                    is_unclear=is_unclear,
                )
            )

        doc.close()
        return pages

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_pdf_str(file_bytes: bytes) -> str:
    """
    Direct string-only convenience function for legacy callers.
    Returns plain text with [Page X] markers preserved.
    """
    pages = extract_text_from_pdf(file_bytes)
    return pages.to_text()


def split_into_chunks(
    text: str,
    max_chars: int = 18000,
    max_tokens: int | None = None,
) -> list[dict]:
    """
    Split document text into chunks, preserving page boundaries.
    Each chunk includes metadata about which pages it covers.
    Returns list of: { text, start_page, end_page, chunk_index }

    If max_tokens is provided, delegates to token-aware ChunkingService.
    Otherwise, preserves the legacy character-based chunking.
    """
    if max_tokens is not None:
        from services.chunking_service import ChunkingService
        service = ChunkingService(max_chunk_tokens=max_tokens)
        return [c.to_dict() for c in service.chunk_text(text)]

    chunks = []
    current_chunk = []
    current_chars = 0
    current_start_page = 1
    current_page = 1
    chunk_index = 0

    lines = text.split('\n')

    for line in lines:
        page_match = re.match(r'\[Page (\d+)\]', line)
        if page_match:
            current_page = int(page_match.group(1))
            if chunk_index == 0 and not current_chunk:
                current_start_page = current_page

        line_len = len(line) + 1

        if current_chars + line_len > max_chars and current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'start_page': current_start_page,
                'end_page': current_page,
                'chunk_index': chunk_index,
            })
            chunk_index += 1
            current_start_page = current_page
            current_chunk = [line]
            current_chars = line_len
        else:
            current_chunk.append(line)
            current_chars += line_len

    if current_chunk:
        chunks.append({
            'text': '\n'.join(current_chunk),
            'start_page': current_start_page,
            'end_page': current_page,
            'chunk_index': chunk_index,
        })

    return chunks


# Unicode blocks for the major scripts used in Indian legal documents.
_INDIC_RANGES = [
    (0x0900, 0x097F, "Hindi / Marathi (Devanagari)"),
    (0x0980, 0x09FF, "Bengali / Assamese"),
    (0x0A00, 0x0A7F, "Punjabi (Gurmukhi)"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B00, 0x0B7F, "Odia"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0600, 0x06FF, "Urdu (Arabic script)"),
]


def detect_script(text: str) -> str:
    """Best-guess script/language of the extracted text (for display + messaging)."""
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for lo, hi, name in _INDIC_RANGES:
            if lo <= cp <= hi:
                counts[name] = counts.get(name, 0) + 1
                break
    if not counts:
        return "Latin / English"
    return max(counts, key=counts.get)


def assess_readability(text: str) -> dict:
    """
    Decide whether extracted text is real readable prose (English OR any Indic
    script) versus unreadable output from a scanned image / non-Unicode font.

    Returns {readable: bool, reason: 'ok'|'empty'|'garbled', script: str}.
    `str.isalpha()` is Unicode-aware, so Devanagari/Tamil/Telugu letters count as
    real letters — only empty or symbol-soup extractions are rejected.
    """
    stripped = text.strip()
    if not stripped:
        return {"readable": False, "reason": "empty", "script": ""}

    letters = sum(1 for ch in stripped if ch.isalpha())
    non_space = sum(1 for ch in stripped if not ch.isspace())
    if non_space == 0:
        return {"readable": False, "reason": "empty", "script": ""}

    ratio = letters / non_space
    script = detect_script(stripped)
    if letters < 20 or ratio < 0.4:
        return {"readable": False, "reason": "garbled", "script": script}
    return {"readable": True, "reason": "ok", "script": script}


def get_pdf_metadata(file_bytes: bytes) -> dict:
    """Extract basic metadata from a PDF."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        meta = doc.metadata
        page_count = len(doc)
        doc.close()
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "page_count": page_count,
        }
    except Exception:
        return {"title": "", "author": "", "page_count": 0}


def count_approximate_tokens(text: str) -> int:
    """Rough token count estimate (4 chars per token)."""
    return len(text) // 4
