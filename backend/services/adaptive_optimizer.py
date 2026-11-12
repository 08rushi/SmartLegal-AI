"""
adaptive_optimizer.py — Adaptive Document Optimization Engine & Quality Gate (Phase 6).

Implements:
1. OptimizationTelemetry metadata tracking.
2. Level 1: Lossless PDF stream optimization (clean, deflate, garbage collection).
3. Level 2: Targeted raster image stream downsampling & JPEG compression.
4. Level 3: Rigorous Technical Readability / Representation Quality Gate.
5. Fail-open fallback to original document bytes on rejection or error.

ARCHITECTURAL MANDATE:
The optimization quality score is strictly an optical, structural, and character-survival
readability heuristic. NO CLAIM OF LEGAL ACCURACY IS MADE BY THE OPTIMIZATION QUALITY SCORE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import io
import math
import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

# Decompression bomb safety guard (Section O)
Image.MAX_IMAGE_PIXELS = 80_000_000

from config import get_settings
from services.document_inspector import (
    DocumentProfile,
    DocumentSuitabilityInspector,
    detect_color_stamps_or_seals,
)
from services.pdf_parser import extract_text_from_pdf


@dataclass
class OptimizationTelemetry:
    """Structured telemetry metadata capturing optimization results."""
    original_size_bytes: int
    optimized_size_bytes: int
    optimization_applied: bool
    optimization_method: str       # "none" | "lossless" | "image_stream" | "page_split" | "reverted"
    pages_optimized: int
    pages_split: int
    optimization_reason: str
    technical_quality_score: float
    technical_readability_metrics: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    fallback_to_original_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_size_bytes": self.original_size_bytes,
            "optimized_size_bytes": self.optimized_size_bytes,
            "compression_ratio": (
                round(self.optimized_size_bytes / max(self.original_size_bytes, 1), 4)
                if self.optimization_applied
                else 1.0
            ),
            "optimization_applied": self.optimization_applied,
            "optimization_method": self.optimization_method,
            "pages_optimized": self.pages_optimized,
            "pages_split": self.pages_split,
            "optimization_reason": self.optimization_reason,
            "technical_quality_score": round(self.technical_quality_score, 4),
            "technical_readability_metrics": self.technical_readability_metrics,
            "duration_ms": round(self.duration_ms, 2),
            "fallback_to_original_reason": self.fallback_to_original_reason,
        }


@dataclass(frozen=True)
class QualityGateResult:
    """Outcome of technical readability acceptance verification."""
    accepted: bool
    rejection_reason: Optional[str]
    original_char_count: int
    optimized_char_count: int
    original_quality_score: float
    optimized_quality_score: float
    min_image_dimension: int
    min_image_dpi: float


class TechnicalQualityGate:
    """
    Verifies representation quality and technical readability.
    Does NOT assert legal validity or semantic correctness.
    """

    def __init__(self):
        self.settings = get_settings()

    def evaluate(
        self,
        original_bytes: bytes,
        optimized_bytes: bytes,
        profile: DocumentProfile,
    ) -> QualityGateResult:
        """
        Evaluate optimization output against strict acceptance criteria:
        1. Negative compression rejection (optimized >= original).
        2. Native text loss rejection (> configured tolerance).
        3. Readability score degradation rejection (> configured tolerance).
        4. Resolution floor violation (< 1024px or < 150 DPI).
        """
        orig_size = len(original_bytes)
        opt_size = len(optimized_bytes)

        # Rule 1: Negative Compression
        if opt_size >= orig_size:
            return QualityGateResult(
                accepted=False,
                rejection_reason=f"Negative compression: optimized size ({opt_size} B) >= original size ({orig_size} B).",
                original_char_count=0,
                optimized_char_count=0,
                original_quality_score=0.0,
                optimized_quality_score=0.0,
                min_image_dimension=0,
                min_image_dpi=0.0,
            )

        if not profile.is_pdf:
            # Standalone image validation
            try:
                with Image.open(io.BytesIO(optimized_bytes)) as img_opt:
                    w_opt, h_opt = img_opt.size
                    min_dim = min(w_opt, h_opt)
                    dpi_val = img_opt.info.get("dpi", (72, 72))
                    dpi = max(dpi_val) if isinstance(dpi_val, tuple) else float(dpi_val or 72)

                orig_min_dim = min(profile.max_image_dimensions) if profile.max_image_dimensions != (0, 0) else 0

                # Resolution floor check: if original was >= 1024px, optimized must not drop below 1024px
                if orig_min_dim >= 1024 and min_dim < 1024:
                    return QualityGateResult(
                        accepted=False,
                        rejection_reason=f"Resolution floor violation: image dimension {min_dim}px < 1024px.",
                        original_char_count=0,
                        optimized_char_count=0,
                        original_quality_score=1.0,
                        optimized_quality_score=0.8,
                        min_image_dimension=min_dim,
                        min_image_dpi=dpi,
                    )

                return QualityGateResult(
                    accepted=True,
                    rejection_reason=None,
                    original_char_count=0,
                    optimized_char_count=0,
                    original_quality_score=1.0,
                    optimized_quality_score=1.0,
                    min_image_dimension=min_dim,
                    min_image_dpi=dpi,
                )
            except Exception as exc:
                return QualityGateResult(
                    accepted=False,
                    rejection_reason=f"Failed to inspect optimized image: {exc}",
                    original_char_count=0,
                    optimized_char_count=0,
                    original_quality_score=0.0,
                    optimized_quality_score=0.0,
                    min_image_dimension=0,
                    min_image_dpi=0.0,
                )

        # PDF Validation:
        try:
            orig_pages = extract_text_from_pdf(original_bytes)
            opt_pages = extract_text_from_pdf(optimized_bytes)
        except Exception as exc:
            return QualityGateResult(
                accepted=False,
                rejection_reason=f"PDF extraction error during quality evaluation: {exc}",
                original_char_count=0,
                optimized_char_count=0,
                original_quality_score=0.0,
                optimized_quality_score=0.0,
                min_image_dimension=0,
                min_image_dpi=0.0,
            )

        orig_chars = sum(len(p.text) for p in orig_pages)
        opt_chars = sum(len(p.text) for p in opt_pages)

        orig_q = (
            sum(p.quality_score for p in orig_pages) / max(len(orig_pages), 1)
        )
        opt_q = (
            sum(p.quality_score for p in opt_pages) / max(len(opt_pages), 1)
        )

        # Rule 2: Native Text Loss
        # If original had extractable characters, verify that character count did not drop > tolerance
        if orig_chars > 50:
            char_loss_ratio = (orig_chars - opt_chars) / orig_chars
            if char_loss_ratio > self.settings.optimization_text_loss_tolerance:
                return QualityGateResult(
                    accepted=False,
                    rejection_reason=(
                        f"Native text loss exceeds tolerance: lost {char_loss_ratio:.2%} of characters "
                        f"(original: {orig_chars}, optimized: {opt_chars})."
                    ),
                    original_char_count=orig_chars,
                    optimized_char_count=opt_chars,
                    original_quality_score=orig_q,
                    optimized_quality_score=opt_q,
                    min_image_dimension=0,
                    min_image_dpi=0.0,
                )

        # Rule 3: Readability Metric Degradation
        if orig_q > 0.1:
            q_drop = orig_q - opt_q
            if q_drop > self.settings.optimization_quality_delta_tolerance:
                return QualityGateResult(
                    accepted=False,
                    rejection_reason=(
                        f"Technical readability score degraded beyond allowed tolerance "
                        f"(original: {orig_q:.3f}, optimized: {opt_q:.3f}, drop: {q_drop:.3f})."
                    ),
                    original_char_count=orig_chars,
                    optimized_char_count=opt_chars,
                    original_quality_score=orig_q,
                    optimized_quality_score=opt_q,
                    min_image_dimension=0,
                    min_image_dpi=0.0,
                )

        # Rule 4: Resolution Floor Violation
        # Inspect images in optimized PDF to ensure they weren't crushed below OCR floors
        min_dim_found = 999999
        min_dpi_found = 999999.0
        has_images_in_opt = False

        try:
            doc_opt = fitz.open(stream=optimized_bytes, filetype="pdf")
            for page_idx in range(doc_opt.page_count):
                page = doc_opt.load_page(page_idx)
                page_rect = page.rect
                page_w_pt = max(page_rect.width, 1.0)
                page_h_pt = max(page_rect.height, 1.0)
                for img_info in page.get_images(full=True):
                    xref = img_info[0]
                    base_img = doc_opt.extract_image(xref)
                    if base_img:
                        has_images_in_opt = True
                        w = base_img.get("width", 0)
                        h = base_img.get("height", 0)
                        dim = min(w, h)
                        if dim < min_dim_found:
                            min_dim_found = dim
                        xres = base_img.get("xres", 0)
                        yres = base_img.get("yres", 0)
                        rendered_dpi_x = (w / page_w_pt) * 72.0
                        rendered_dpi_y = (h / page_h_pt) * 72.0
                        dpi = max(xres, yres, rendered_dpi_x, rendered_dpi_y)
                        if dpi < min_dpi_found:
                            min_dpi_found = dpi
            doc_opt.close()
        except Exception:
            pass

        if has_images_in_opt:
            # Check if source document originally had large images (dimensions >= 1024 or DPI >= 150)
            orig_had_high_res = (
                max(profile.max_image_dimensions) >= 1024 or profile.max_image_dpi >= 150.0
            )
            if orig_had_high_res:
                if min_dim_found < 1024:
                    return QualityGateResult(
                        accepted=False,
                        rejection_reason=f"Resolution floor violation: image dimension {min_dim_found}px below threshold.",
                        original_char_count=orig_chars,
                        optimized_char_count=opt_chars,
                        original_quality_score=orig_q,
                        optimized_quality_score=opt_q,
                        min_image_dimension=min_dim_found,
                        min_image_dpi=min_dpi_found if min_dpi_found < 999999 else 0.0,
                    )
                if min_dpi_found < self.settings.optimization_min_dpi and profile.max_image_dpi >= self.settings.optimization_min_dpi:
                    return QualityGateResult(
                        accepted=False,
                        rejection_reason=f"Resolution floor violation: image DPI {min_dpi_found:.1f} below minimum {self.settings.optimization_min_dpi}.",
                        original_char_count=orig_chars,
                        optimized_char_count=opt_chars,
                        original_quality_score=orig_q,
                        optimized_quality_score=opt_q,
                        min_image_dimension=min_dim_found,
                        min_image_dpi=min_dpi_found,
                    )

        # All acceptance gates passed
        return QualityGateResult(
            accepted=True,
            rejection_reason=None,
            original_char_count=orig_chars,
            optimized_char_count=opt_chars,
            original_quality_score=orig_q,
            optimized_quality_score=opt_q,
            min_image_dimension=min_dim_found if has_images_in_opt else 0,
            min_image_dpi=min_dpi_found if (has_images_in_opt and min_dpi_found < 999999) else 0.0,
        )


class AdaptiveOptimizationEngine:
    """
    Orchestrates lossless and targeted image stream optimization with deterministic quality gates.
    """

    def __init__(self):
        self.settings = get_settings()
        self.inspector = DocumentSuitabilityInspector()
        self.quality_gate = TechnicalQualityGate()

    def optimize(
        self,
        content: bytes,
        filename: str = "",
        profile: Optional[DocumentProfile] = None,
    ) -> Tuple[bytes, OptimizationTelemetry]:
        """
        Adaptively optimize document bytes.
        Returns:
            Tuple of (output_bytes, OptimizationTelemetry).
            If optimization fails, is rejected, or is not recommended, original bytes are returned.
        """
        start_time = time.perf_counter()
        orig_size = len(content)

        if profile is None:
            profile = self.inspector.inspect(content, filename)

        # Baseline telemetry if bypassed
        base_telemetry = OptimizationTelemetry(
            original_size_bytes=orig_size,
            optimized_size_bytes=orig_size,
            optimization_applied=False,
            optimization_method="none",
            pages_optimized=0,
            pages_split=0,
            optimization_reason=profile.reason,
            technical_quality_score=1.0,
            technical_readability_metrics={
                "document_type": profile.document_type,
                "page_count": profile.page_count,
            },
            duration_ms=0.0,
            fallback_to_original_reason=None,
        )

        if not self.settings.optimization_enabled:
            base_telemetry.optimization_reason = "Optimization disabled by configuration."
            base_telemetry.duration_ms = (time.perf_counter() - start_time) * 1000.0
            return content, base_telemetry

        if profile.recommended_strategy == "pass_through":
            base_telemetry.duration_ms = (time.perf_counter() - start_time) * 1000.0
            return content, base_telemetry

        if profile.recommended_strategy == "reject":
            base_telemetry.fallback_to_original_reason = profile.reason
            base_telemetry.duration_ms = (time.perf_counter() - start_time) * 1000.0
            return content, base_telemetry

        try:
            # ── Level 1: Lossless Stream Optimization ─────────────────────────
            if profile.recommended_strategy == "lossless":
                opt_bytes = self._lossless_optimize_pdf(content)
                gate = self.quality_gate.evaluate(content, opt_bytes, profile)
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                if gate.accepted:
                    telemetry = OptimizationTelemetry(
                        original_size_bytes=orig_size,
                        optimized_size_bytes=len(opt_bytes),
                        optimization_applied=True,
                        optimization_method="lossless",
                        pages_optimized=profile.page_count,
                        pages_split=0,
                        optimization_reason="Lossless stream compression and orphan object garbage collection.",
                        technical_quality_score=gate.optimized_quality_score,
                        technical_readability_metrics={
                            "char_count": gate.optimized_char_count,
                            "original_quality": gate.original_quality_score,
                        },
                        duration_ms=duration_ms,
                    )
                    return opt_bytes, telemetry
                else:
                    base_telemetry.optimization_method = "reverted"
                    base_telemetry.fallback_to_original_reason = gate.rejection_reason
                    base_telemetry.duration_ms = duration_ms
                    return content, base_telemetry

            # ── Level 2: Targeted Image Stream Optimization ───────────────────
            if profile.recommended_strategy == "image_stream":
                if profile.is_pdf:
                    opt_bytes, pages_count = self._optimize_pdf_image_streams(content, profile)
                else:
                    opt_bytes = self._optimize_standalone_image(content, profile)
                    pages_count = 1

                gate = self.quality_gate.evaluate(content, opt_bytes, profile)
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                if gate.accepted:
                    telemetry = OptimizationTelemetry(
                        original_size_bytes=orig_size,
                        optimized_size_bytes=len(opt_bytes),
                        optimization_applied=True,
                        optimization_method="image_stream",
                        pages_optimized=pages_count,
                        pages_split=0,
                        optimization_reason="Targeted image downsampling and quality-preserving compression.",
                        technical_quality_score=gate.optimized_quality_score,
                        technical_readability_metrics={
                            "char_count": gate.optimized_char_count,
                            "min_image_dim": gate.min_image_dimension,
                            "min_image_dpi": gate.min_image_dpi,
                        },
                        duration_ms=duration_ms,
                    )
                    return opt_bytes, telemetry
                else:
                    base_telemetry.optimization_method = "reverted"
                    base_telemetry.fallback_to_original_reason = gate.rejection_reason
                    base_telemetry.duration_ms = duration_ms
                    return content, base_telemetry

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            base_telemetry.optimization_method = "reverted"
            base_telemetry.fallback_to_original_reason = f"Optimization process error: {exc}"
            base_telemetry.duration_ms = duration_ms
            return content, base_telemetry

        base_telemetry.duration_ms = (time.perf_counter() - start_time) * 1000.0
        return content, base_telemetry

    def _lossless_optimize_pdf(self, content: bytes) -> bytes:
        """
        Lossless optimization:
        Runs garbage collection (4), deflate (True), and stream cleaning.
        Leaves all vector text and font definitions 100% intact.
        """
        doc = fitz.open(stream=content, filetype="pdf")
        buf = io.BytesIO()
        doc.save(buf, clean=True, deflate=True, garbage=4)
        doc.close()
        return buf.getvalue()

    def _optimize_pdf_image_streams(
        self, content: bytes, profile: DocumentProfile
    ) -> Tuple[bytes, int]:
        """
        Targeted raster image stream optimization:
        Iterates across pages and replaces high-resolution image streams with
        downsampled representations while strictly leaving text layers intact.
        """
        doc = fitz.open(stream=content, filetype="pdf")
        pages_optimized = 0
        seen_xrefs = set()

        target_dpi = self.settings.optimization_target_dpi
        jpeg_quality = self.settings.optimization_jpeg_quality
        min_dpi = self.settings.optimization_min_dpi

        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            page_rect = page.rect
            page_w_pt = max(page_rect.width, 1.0)
            page_h_pt = max(page_rect.height, 1.0)

            image_infos = page.get_images(full=True)
            page_had_opt = False

            for img_info in image_infos:
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                try:
                    base_img = doc.extract_image(xref)
                except Exception:
                    continue

                if not base_img:
                    continue

                img_bytes = base_img.get("image", b"")
                w = base_img.get("width", 0)
                h = base_img.get("height", 0)
                xres = base_img.get("xres", 72)
                yres = base_img.get("yres", 72)
                source_dpi = max(xres, yres, (w / page_w_pt) * 72.0, (h / page_h_pt) * 72.0)

                # Never downscale if already <= min_dpi
                if source_dpi <= min_dpi and w <= 1800 and h <= 1800:
                    continue

                try:
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    # Check for official stamps or seals
                    has_stamps = detect_color_stamps_or_seals(
                        pil_img, self.settings.optimization_color_variance_threshold
                    )

                    # Compute target dimensions
                    scale = min(1.0, target_dpi / max(source_dpi, 1.0))
                    new_w = max(int(w * scale), 1024)
                    new_h = max(int(h * scale), 1024)

                    if new_w < w or new_h < h:
                        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # Preservation of color stamps:
                    # If stamps detected, ensure RGB and quality >= 85
                    out_buf = io.BytesIO()
                    save_dpi = (int(target_dpi), int(target_dpi))
                    if has_stamps:
                        rgb_img = pil_img.convert("RGB")
                        rgb_img.save(out_buf, format="JPEG", quality=max(jpeg_quality, 85), optimize=True, dpi=save_dpi)
                    else:
                        # If image is grayscale or monochromatic text, convert to L
                        if pil_img.mode in ("L", "1"):
                            pil_img.save(out_buf, format="JPEG", quality=jpeg_quality, optimize=True, dpi=save_dpi)
                        else:
                            rgb_img = pil_img.convert("RGB")
                            rgb_img.save(out_buf, format="JPEG", quality=jpeg_quality, optimize=True, dpi=save_dpi)

                    new_bytes = out_buf.getvalue()
                    if len(new_bytes) < len(img_bytes):
                        page.replace_image(xref, stream=new_bytes)
                        page_had_opt = True
                except Exception:
                    continue

            if page_had_opt:
                pages_optimized += 1

        buf = io.BytesIO()
        doc.save(buf, clean=True, deflate=True, garbage=4)
        doc.close()
        return buf.getvalue(), pages_optimized

    def _optimize_standalone_image(
        self, content: bytes, profile: DocumentProfile
    ) -> bytes:
        """
        Optimizes standalone raster image file.
        """
        target_dpi = self.settings.optimization_target_dpi
        jpeg_quality = self.settings.optimization_jpeg_quality

        with Image.open(io.BytesIO(content)) as img:
            w, h = img.size
            has_stamps = detect_color_stamps_or_seals(
                img, self.settings.optimization_color_variance_threshold
            )

            # Max dimension clamp for OCR envelope: 2200 px
            max_dim = max(w, h)
            if max_dim > 2200:
                scale = 2200.0 / max_dim
                new_w = max(int(w * scale), 1024)
                new_h = max(int(h * scale), 1024)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            rgb_img = img.convert("RGB")
            quality = max(jpeg_quality, 85) if has_stamps else jpeg_quality
            rgb_img.save(out_buf, format="JPEG", quality=quality, optimize=True, dpi=(target_dpi, target_dpi))
            return out_buf.getvalue()
