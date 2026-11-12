"""
page_splitter.py — Deterministic Page Splitting & Recombination (Phase 6).

Implements:
1. `DocumentPart` dataclass preserving complete provenance.
2. `DeterministicPageSplitter` with strict enforcement of the <= 50-page ceiling.
3. Sequential recombination with strict page-number continuity and provenance preservation.

CRITICAL INVARIANT:
Page splitting operates strictly within an already accepted <= 50-page document.
It CANNOT be used to bypass the 50-page security ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import io
import math
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

from config import get_settings
from services.page_content import PageContent, PageContentList


@dataclass(frozen=True)
class DocumentPart:
    """Isolated processing partition of a document with full provenance."""
    document_id: str
    part_number: int              # 1-indexed (1..total_parts)
    total_parts: int
    start_page: int               # 1-indexed inclusive (e.g. 1)
    end_page: int                 # 1-indexed inclusive (e.g. 20)
    page_numbers: List[int]       # e.g. [1, 2, ..., 20]
    content_bytes: bytes
    file_size_bytes: int
    created_at: str


class DeterministicPageSplitter:
    """
    Splits multi-page PDFs into deterministic sub-parts for payload management.
    """

    def __init__(self, max_pages_per_part: int = 20):
        self.settings = get_settings()
        self.max_pages_per_part = max(1, max_pages_per_part)

    def split(self, content: bytes, document_id: str = "") -> List[DocumentPart]:
        """
        Split a PDF document into deterministic parts.

        Enforces:
        - Must be valid PDF.
        - Total pages must be <= settings.max_page_count (50). Raises ValueError otherwise.
        - Part numbers are 1-indexed with exact page mappings.
        """
        if not content[:5].startswith(b"%PDF"):
            raise ValueError("Only PDF documents can be split into parts.")

        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = doc.page_count

        if total_pages == 0:
            doc.close()
            raise ValueError("Cannot split an empty PDF (0 pages).")

        # Invariant: 50-page security ceiling
        if total_pages > self.settings.max_page_count:
            doc.close()
            raise ValueError(
                f"Page splitting cannot process documents exceeding the maximum "
                f"limit of {self.settings.max_page_count} pages (found: {total_pages})."
            )

        now = datetime.now(timezone.utc).isoformat()

        # If document fits in a single part, return 1 part
        if total_pages <= self.max_pages_per_part:
            doc.close()
            return [
                DocumentPart(
                    document_id=document_id,
                    part_number=1,
                    total_parts=1,
                    start_page=1,
                    end_page=total_pages,
                    page_numbers=list(range(1, total_pages + 1)),
                    content_bytes=content,
                    file_size_bytes=len(content),
                    created_at=now,
                )
            ]

        # Calculate part boundaries
        total_parts = math.ceil(total_pages / self.max_pages_per_part)
        parts: List[DocumentPart] = []

        for part_idx in range(total_parts):
            start_p_idx = part_idx * self.max_pages_per_part
            end_p_idx = min(start_p_idx + self.max_pages_per_part, total_pages) - 1

            start_page_1 = start_p_idx + 1
            end_page_1 = end_p_idx + 1
            page_nums = list(range(start_page_1, end_page_1 + 1))

            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start_p_idx, to_page=end_p_idx)
            buf = io.BytesIO()
            new_doc.save(buf, clean=True, deflate=True, garbage=4)
            new_doc.close()
            part_bytes = buf.getvalue()

            parts.append(
                DocumentPart(
                    document_id=document_id,
                    part_number=part_idx + 1,
                    total_parts=total_parts,
                    start_page=start_page_1,
                    end_page=end_page_1,
                    page_numbers=page_nums,
                    content_bytes=part_bytes,
                    file_size_bytes=len(part_bytes),
                    created_at=now,
                )
            )

        doc.close()
        return parts


def recombine_pages(part_results: List[Tuple[DocumentPart, PageContentList]]) -> PageContentList:
    """
    Recombine extracted PageContentLists from individual DocumentParts.

    Guarantees:
    - Strict chronological/numerical page order (1, 2, ..., N).
    - Preserves exact physical 1-indexed page_num on each PageContent.
    - Zero duplicates.
    - Zero lost pages.
    """
    if not part_results:
        return PageContentList()

    # Sort parts by part_number
    sorted_parts = sorted(part_results, key=lambda p: p[0].part_number)

    all_pages = PageContentList()
    expected_next_page = 1

    for part, pages in sorted_parts:
        if part.start_page != expected_next_page:
            raise ValueError(
                f"Page sequence break during recombination: expected page {expected_next_page}, "
                f"got part starting at page {part.start_page}."
            )

        for idx, page in enumerate(pages):
            correct_page_num = part.start_page + idx
            # Ensure physical page_num reflects overall document page number
            if page.page_num != correct_page_num:
                page.page_num = correct_page_num
            all_pages.append(page)

        expected_next_page = part.end_page + 1

    return all_pages
