"""
document_inspector.py — Document Suitability Inspection (Phase 6).

Inspects incoming documents (PDF and images) using observable structural
and technical characteristics without relying on a naive file-size shortcut.

Contrast Scenarios:
- 15 MB Digital Text PDF:
    vector text density is high, embedded image bytes are small -> "pass_through"
- 7 MB Scanned PDF:
    contains 600 DPI uncompressed scan pages -> "image_stream"
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

from config import get_settings
from services.pdf_parser import extract_text_from_pdf


@dataclass(frozen=True)
class DocumentProfile:
    """Observable structural and technical characteristics of a document."""
    file_size_bytes: int
    page_count: int
    is_pdf: bool
    document_type: str             # "digital_pdf" | "scanned_pdf" | "mixed_pdf" | "image"
    embedded_image_count: int
    total_image_bytes: int
    max_image_dimensions: Tuple[int, int]
    max_image_dpi: float
    has_color_stamps_or_seals: bool
    is_technically_suitable: bool
    recommended_strategy: str       # "pass_through" | "lossless" | "image_stream" | "page_split"
    reason: str


def detect_color_stamps_or_seals(image: Image.Image, variance_threshold: float = 12.0) -> bool:
    """
    Detect whether an image contains colored official stamps, seals, or signatures.
    Samples non-background/non-monochrome pixels to evaluate channel divergence.
    """
    if image.mode not in ("RGB", "RGBA"):
        return False

    thumb = image.copy()
    thumb.thumbnail((200, 200))
    rgb_thumb = thumb.convert("RGB")
    pixels = list(rgb_thumb.getdata())

    colored_pixels = 0
    evaluated_pixels = 0

    for r, g, b in pixels:
        # Ignore paper background (near-white) and dark text (near-black)
        if (r > 225 and g > 225 and b > 225) or (r < 45 and g < 45 and b < 45):
            continue
        evaluated_pixels += 1
        diff = max(abs(r - g), abs(g - b), abs(b - r))
        if diff >= variance_threshold:
            colored_pixels += 1

    # If at least 0.5% of total thumbnail pixels (or >2% of evaluated non-bg pixels) show color
    if colored_pixels >= max(15, int(len(pixels) * 0.005)):
        return True
    return False


class DocumentSuitabilityInspector:
    """
    Deterministic inspector that profiles documents and recommends optimization strategies.
    """

    def __init__(self):
        self.settings = get_settings()

    def inspect(self, content: bytes, filename: str = "") -> DocumentProfile:
        """
        Inspect raw document bytes and generate a comprehensive DocumentProfile.
        """
        file_size = len(content)
        is_pdf = content[:5].startswith(b"%PDF")

        if is_pdf:
            return self._inspect_pdf(content, filename)
        else:
            return self._inspect_image(content, filename)

    def _inspect_pdf(self, content: bytes, filename: str) -> DocumentProfile:
        file_size = len(content)
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            page_count = doc.page_count
        except Exception as e:
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=0,
                is_pdf=True,
                document_type="unsupported",
                embedded_image_count=0,
                total_image_bytes=0,
                max_image_dimensions=(0, 0),
                max_image_dpi=0.0,
                has_color_stamps_or_seals=False,
                is_technically_suitable=False,
                recommended_strategy="pass_through",
                reason=f"Document is corrupted or cannot be parsed as PDF: {e}",
            )

        # Check 50-page ceiling
        if page_count > self.settings.max_page_count:
            doc.close()
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=page_count,
                is_pdf=True,
                document_type="unsupported",
                embedded_image_count=0,
                total_image_bytes=0,
                max_image_dimensions=(0, 0),
                max_image_dpi=0.0,
                has_color_stamps_or_seals=False,
                is_technically_suitable=False,
                recommended_strategy="reject",
                reason=f"Document exceeds maximum limit of {self.settings.max_page_count} pages.",
            )

        # Reuse Phase 2 page classification logic
        try:
            pages_list = extract_text_from_pdf(content)
            doc_type = pages_list.document_type  # "digital_pdf" | "scanned_pdf" | "mixed_pdf"
        except Exception:
            doc_type = "unsupported"

        # Inspect embedded image streams across pages
        total_images = 0
        total_image_bytes = 0
        max_width = 0
        max_height = 0
        max_dpi = 0.0
        has_color_stamps = False
        seen_xrefs = set()

        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            page_rect = page.rect
            page_w_pt = max(page_rect.width, 1.0)
            page_h_pt = max(page_rect.height, 1.0)

            image_infos = page.get_images(full=True)
            for img_info in image_infos:
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                total_images += 1

                try:
                    base_img = doc.extract_image(xref)
                except Exception:
                    continue

                if not base_img:
                    continue

                img_bytes = base_img.get("image", b"")
                total_image_bytes += len(img_bytes)
                w = base_img.get("width", 0)
                h = base_img.get("height", 0)
                if w > max_width:
                    max_width = w
                if h > max_height:
                    max_height = h

                # Estimate DPI
                xres = base_img.get("xres", 0)
                yres = base_img.get("yres", 0)
                reported_dpi = max(xres, yres)

                # Compute rendered DPI relative to page size in points (1 pt = 1/72 inch)
                rendered_dpi_x = (w / page_w_pt) * 72.0
                rendered_dpi_y = (h / page_h_pt) * 72.0
                effective_dpi = max(reported_dpi, rendered_dpi_x, rendered_dpi_y)
                if effective_dpi > max_dpi:
                    max_dpi = effective_dpi

                # Check for colored stamps/seals if image is RGB/RGBA
                if not has_color_stamps and img_bytes:
                    try:
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        if detect_color_stamps_or_seals(
                            pil_img, self.settings.optimization_color_variance_threshold
                        ):
                            has_color_stamps = True
                    except Exception:
                        pass

        doc.close()

        # Decision Logic:
        # 1. Page splitting: If document is scanned/mixed and total payload exceeds provider ceiling (> 18 MB)
        #    and page count >= 20, recommend page splitting to ensure individual visual API payloads succeed.
        max_provider_payload_bytes = 18 * 1024 * 1024
        if file_size > max_provider_payload_bytes and doc_type in ("scanned_pdf", "mixed_pdf") and page_count >= 20:
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=page_count,
                is_pdf=True,
                document_type=doc_type,
                embedded_image_count=total_images,
                total_image_bytes=total_image_bytes,
                max_image_dimensions=(max_width, max_height),
                max_image_dpi=round(max_dpi, 1),
                has_color_stamps_or_seals=has_color_stamps,
                is_technically_suitable=False,
                recommended_strategy="page_split",
                reason="Large scanned PDF payload exceeds provider limits; requires deterministic page splitting.",
            )

        # 2. Contrast Scenario 1: Digital PDF
        # High vector text density, small or zero embedded raster images.
        # Native PyMuPDF handles it in milliseconds without rasterization.
        if doc_type == "digital_pdf":
            # If embedded image bytes are minimal (< 3 MB) or images are small logos (< 220 DPI)
            if total_image_bytes < 3 * 1024 * 1024 or max_dpi <= 220:
                return DocumentProfile(
                    file_size_bytes=file_size,
                    page_count=page_count,
                    is_pdf=True,
                    document_type=doc_type,
                    embedded_image_count=total_images,
                    total_image_bytes=total_image_bytes,
                    max_image_dimensions=(max_width, max_height),
                    max_image_dpi=round(max_dpi, 1),
                    has_color_stamps_or_seals=has_color_stamps,
                    is_technically_suitable=True,
                    recommended_strategy="pass_through",
                    reason="Digital PDF with high native text density and acceptable raster footprint; pass through unmodified.",
                )

        # 3. Contrast Scenario 2: Scanned PDF or Image-Heavy PDF
        # High DPI or massive image dimensions (e.g. 600 DPI scan, raw TIFFs)
        # Needs downsampling to safe target DPI to avoid OOM in OCR engines.
        if (
            max_dpi > (self.settings.optimization_target_dpi + 40)
            or max_width > 2400
            or max_height > 2400
            or (doc_type in ("scanned_pdf", "mixed_pdf") and file_size > 5 * 1024 * 1024)
        ):
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=page_count,
                is_pdf=True,
                document_type=doc_type,
                embedded_image_count=total_images,
                total_image_bytes=total_image_bytes,
                max_image_dimensions=(max_width, max_height),
                max_image_dpi=round(max_dpi, 1),
                has_color_stamps_or_seals=has_color_stamps,
                is_technically_suitable=False,
                recommended_strategy="image_stream",
                reason="Document contains high-DPI or oversized raster images requiring targeted downsampling.",
            )

        # 4. Moderate size PDF with potential metadata bloat / orphan objects
        threshold_bytes = int(self.settings.optimization_threshold_mb * 1024 * 1024)
        if file_size > threshold_bytes:
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=page_count,
                is_pdf=True,
                document_type=doc_type,
                embedded_image_count=total_images,
                total_image_bytes=total_image_bytes,
                max_image_dimensions=(max_width, max_height),
                max_image_dpi=round(max_dpi, 1),
                has_color_stamps_or_seals=has_color_stamps,
                is_technically_suitable=False,
                recommended_strategy="lossless",
                reason="Document exceeds optimization threshold; lossless stream compression recommended.",
            )

        # 5. Default: Within all performance and resolution constraints
        return DocumentProfile(
            file_size_bytes=file_size,
            page_count=page_count,
            is_pdf=True,
            document_type=doc_type,
            embedded_image_count=total_images,
            total_image_bytes=total_image_bytes,
            max_image_dimensions=(max_width, max_height),
            max_image_dpi=round(max_dpi, 1),
            has_color_stamps_or_seals=has_color_stamps,
            is_technically_suitable=True,
            recommended_strategy="pass_through",
            reason="Document is within all technical and performance bounds.",
        )

    def _inspect_image(self, content: bytes, filename: str) -> DocumentProfile:
        file_size = len(content)
        try:
            with Image.open(io.BytesIO(content)) as img:
                w, h = img.size
                dpi_tuple = img.info.get("dpi", (72, 72))
                dpi = max(dpi_tuple) if isinstance(dpi_tuple, tuple) else float(dpi_tuple or 72)
                has_color = detect_color_stamps_or_seals(
                    img, self.settings.optimization_color_variance_threshold
                )
        except Exception:
            return DocumentProfile(
                file_size_bytes=file_size,
                page_count=1,
                is_pdf=False,
                document_type="image",
                embedded_image_count=1,
                total_image_bytes=file_size,
                max_image_dimensions=(0, 0),
                max_image_dpi=0.0,
                has_color_stamps_or_seals=False,
                is_technically_suitable=False,
                recommended_strategy="pass_through",
                reason="Unable to parse image header; passing through to OCR fallback.",
            )

        # Single image payload evaluation:
        # If image exceeds 4 MB or dimensions > 2500 px or DPI > 250 -> image_stream optimization
        needs_optimization = (
            file_size > 4 * 1024 * 1024
            or w > 2500
            or h > 2500
            or dpi > (self.settings.optimization_target_dpi + 40)
        )

        strategy = "image_stream" if needs_optimization else "pass_through"
        reason = (
            "Image dimensions or file size exceed single-page visual processing envelope."
            if needs_optimization
            else "Image is within single-page visual processing envelope."
        )

        return DocumentProfile(
            file_size_bytes=file_size,
            page_count=1,
            is_pdf=False,
            document_type="image",
            embedded_image_count=1,
            total_image_bytes=file_size,
            max_image_dimensions=(w, h),
            max_image_dpi=round(dpi, 1),
            has_color_stamps_or_seals=has_color,
            is_technically_suitable=not needs_optimization,
            recommended_strategy=strategy,
            reason=reason,
        )
