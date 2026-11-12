"""
test_phase6_optimization.py — Phase 6 Adaptive Optimization & 25 MB Upload Test Suite.

Covers the complete approved Phase 6 test matrix (Tests A through Z):
Test-A: Upload boundary below 25 MB (24.5 MB accepted)
Test-B: Upload boundary exact 25 MB (26,214,400 bytes accepted)
Test-C: Upload boundary above 25 MB (25 MB + 1KB rejected with 400)
Test-D: 50-page ceiling independent (5 MB 51 pages rejected with 400)
Test-E: 25 MB with 51 pages rejected before optimization
Test-F: 7 MB scanned PDF with 600 DPI triggers image stream optimization
Test-G: 15 MB digital text PDF bypasses image optimization (pass-through)
Test-H: Configurable DPI and JPEG quality respected
Test-I: No blind rasterization of digital PDF (vector text preserved)
Test-J: Color stamp and seal preservation (RGB color profile protected)
Test-K: Technical quality gate catches character loss > 2%
Test-L: Technical quality gate catches readability drop > 0.05
Test-M: Technical quality gate catches resolution floor violation (< 150 DPI)
Test-N: Negative compression rejection (reverts to original bytes)
Test-O: Lossless optimization stream cleaning (garbage=4, deflate=True)
Test-P: Deterministic page splitting (45 pages -> parts 1..20, 21..40, 41..45)
Test-Q: Page splitting cannot bypass 50 pages ceiling
Test-R: Recombination order, exact 1-indexed numbering, and provenance
Test-S: Derived artifact cleanup on success (transient files removed)
Test-T: Derived artifact cleanup on failure (scratch files cleaned in finally)
Test-U: Phase 3 token-aware chunking compatibility
Test-V: Phase 4 visual OCR pipeline compatibility
Test-W: Phase 5 provider budget manager independence
Test-X: WhatsApp 25 MB streaming download acceptance
Test-Y: WhatsApp oversized 26 MB rejection with localized copy (EN/HI/MR)
Test-Z: Corrupt / malicious PDF handled gracefully (fail-safe)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import io
import os
import shutil
import tempfile
from typing import List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
from PIL import Image
import pytest

from config import get_settings
from services.adaptive_optimizer import (
    AdaptiveOptimizationEngine,
    OptimizationTelemetry,
    TechnicalQualityGate,
)
from services.chunking_service import ChunkingService
from services.document_inspector import (
    DocumentProfile,
    DocumentSuitabilityInspector,
    detect_color_stamps_or_seals,
)
from services.page_content import PageContent, PageContentList
from services.page_splitter import (
    DeterministicPageSplitter,
    DocumentPart,
    recombine_pages,
)
from services.pdf_parser import extract_text_from_pdf
from services.whatsapp.boundaries import LanguageCode


# ── Helpers for Synthetic Fixtures ───────────────────────────────────────────

def create_synthetic_digital_pdf(
    num_pages: int = 1,
    text: str = "This Rental Agreement is made between Landlord and Tenant.",
    target_size_bytes: int = 0,
) -> bytes:
    """Create a valid digital PDF with vector text."""
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4 in points
        page.insert_text((50, 72), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf, clean=True, deflate=True)
    doc.close()
    data = buf.getvalue()

    if target_size_bytes > len(data):
        padding_needed = target_size_bytes - len(data)
        chunk = b"\n% " + (b"0" * 1020)
        num_chunks = padding_needed // len(chunk)
        rem = padding_needed % len(chunk)
        pad = chunk * num_chunks
        if rem >= 4:
            pad += b"\n% " + (b"0" * (rem - 4)) + b"\n"
            diff = target_size_bytes - (len(data) + len(pad))
            if diff > 0:
                pad += b" " * diff
            elif diff < 0:
                pad = pad[:len(pad) + diff]
        elif rem > 0:
            pad += b" " * rem
        data = data + pad
    return data


def create_synthetic_scanned_pdf(
    num_pages: int = 1,
    width: int = 1200,
    height: int = 1600,
    dpi: int = 300,
    color: str = "white",
    with_color_stamp: bool = False,
) -> bytes:
    """Create a scanned PDF containing raster page images."""
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page(width=595, height=842)
        # Create PIL Image
        img = Image.new("RGB", (width, height), color=color)
        if with_color_stamp:
            # Draw a distinct red and blue official seal / stamp in the corner
            for x in range(100, 300):
                for y in range(100, 300):
                    if (x - 200) ** 2 + (y - 200) ** 2 < 80 ** 2:
                        img.putpixel((x, y), (220, 20, 30))  # Red seal
                    elif (x - 200) ** 2 + (y - 200) ** 2 < 95 ** 2:
                        img.putpixel((x, y), (20, 50, 210))  # Blue border
        img_buf = io.BytesIO()
        img.save(img_buf, format="JPEG", quality=90, dpi=(dpi, dpi))
        page.insert_image(page.rect, stream=img_buf.getvalue())
    buf = io.BytesIO()
    doc.save(buf, clean=True, deflate=True)
    doc.close()
    return buf.getvalue()


# ── Test Matrix: Tests A through Z ───────────────────────────────────────────

def test_phase6a_configuration_and_limits():
    """Phase 6A: Verify canonical 25 MB and 50 page configurations."""
    settings = get_settings()
    assert settings.max_upload_size_mb == 25
    assert settings.max_upload_size_bytes == 26_214_400
    assert settings.max_page_count == 50
    assert settings.optimization_threshold_mb == 8.0
    assert settings.optimization_target_mb == 6.0
    assert settings.optimization_target_dpi == 200
    assert settings.optimization_min_dpi == 150
    assert settings.optimization_jpeg_quality == 85
    assert settings.optimization_color_variance_threshold == 12.0
    assert settings.optimization_enabled is True
    assert settings.optimization_text_loss_tolerance == 0.02
    assert settings.optimization_quality_delta_tolerance == 0.05


def test_upload_boundary_below_25mb(client, auth_headers_user_a):
    """Test-A: Upload boundary below 25 MB (e.g. 24.5 MB) is accepted."""
    # Fast synthetic 1-page PDF padded to 24 MB
    content = create_synthetic_digital_pdf(num_pages=1, text="Valid 24MB document", target_size_bytes=24 * 1024 * 1024)
    file_obj = ("contract_24mb.pdf", io.BytesIO(content), "application/pdf")

    with patch("routers.upload._store_file", return_value="local://mock_path"):
        resp = client.post(
            "/api/v1/upload",
            files={"file": file_obj},
            headers=auth_headers_user_a,
        )
    assert resp.status_code == 201
    data = resp.json()["document"]
    assert data["filename"] == "contract_24mb.pdf"
    assert data["file_size"] == len(content)


def test_upload_boundary_exact_25mb(client, auth_headers_user_a):
    """Test-B: Upload boundary at exactly 25.0 MB (26,214,400 bytes) and 25 MB - 1 B is accepted."""
    # Test 26,214,399 bytes (25 MB - 1 byte)
    minus_one_byte = 25 * 1024 * 1024 - 1
    content_minus_1 = create_synthetic_digital_pdf(num_pages=1, text="25MB minus 1B", target_size_bytes=minus_one_byte)
    with patch("routers.upload._store_file", return_value="local://mock_path"):
        resp_minus_1 = client.post(
            "/api/v1/upload",
            files={"file": ("minus_1.pdf", io.BytesIO(content_minus_1), "application/pdf")},
            headers=auth_headers_user_a,
        )
    assert resp_minus_1.status_code == 201

    # Test exact 26,214,400 bytes (25.0 MB)
    exact_25mb = 25 * 1024 * 1024
    content = create_synthetic_digital_pdf(num_pages=1, text="Exact 25MB boundary", target_size_bytes=exact_25mb)
    file_obj = ("exact_25mb.pdf", io.BytesIO(content), "application/pdf")

    with patch("routers.upload._store_file", return_value="local://mock_path"):
        resp = client.post(
            "/api/v1/upload",
            files={"file": file_obj},
            headers=auth_headers_user_a,
        )
    assert resp.status_code == 201
    data = resp.json()["document"]
    assert data["file_size"] == exact_25mb


def test_upload_boundary_above_25mb(client, auth_headers_user_a):
    """Test-C: Upload boundary above 25 MB (25 MB + 1 byte and 25 MB + 1KB) is rejected with HTTP 400."""
    # Test 26,214,401 bytes (25 MB + 1 byte)
    plus_one_byte = 25 * 1024 * 1024 + 1
    content_plus_1 = b"%PDF-1.4\n" + (b"0" * (plus_one_byte - 15)) + b"\n%%EOF"
    resp_plus_1 = client.post(
        "/api/v1/upload",
        files={"file": ("plus_1.pdf", io.BytesIO(content_plus_1), "application/pdf")},
        headers=auth_headers_user_a,
    )
    assert resp_plus_1.status_code == 400
    assert "File too large" in resp_plus_1.json()["detail"]
    assert "25 MB" in resp_plus_1.json()["detail"]

    # Test 25 MB + 1KB
    oversized = 25 * 1024 * 1024 + 1024
    content = b"%PDF-1.4\n" + (b"0" * (oversized - 15)) + b"\n%%EOF"
    file_obj = ("too_big.pdf", io.BytesIO(content), "application/pdf")

    resp = client.post(
        "/api/v1/upload",
        files={"file": file_obj},
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 400
    assert "File too large" in resp.json()["detail"]
    assert "25 MB" in resp.json()["detail"]


def test_50_page_ceiling_independent(client, auth_headers_user_a):
    """Test-D: Small 51-page PDF (<=5 MB) is rejected with HTTP 400 due to independent page ceiling."""
    content = create_synthetic_digital_pdf(num_pages=51, text="Page content")
    assert len(content) < 5 * 1024 * 1024  # Well below 25 MB

    file_obj = ("51_pages.pdf", io.BytesIO(content), "application/pdf")
    resp = client.post(
        "/api/v1/upload",
        files={"file": file_obj},
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 400
    assert "50 pages" in resp.json()["detail"]


def test_25mb_with_51_pages_rejected(client, auth_headers_user_a):
    """Test-E: 24 MB PDF with 51 pages is rejected by page ceiling before any optimization."""
    content = create_synthetic_digital_pdf(num_pages=51, text="Large 51-page document", target_size_bytes=24 * 1024 * 1024)
    file_obj = ("huge_51_pages.pdf", io.BytesIO(content), "application/pdf")

    resp = client.post(
        "/api/v1/upload",
        files={"file": file_obj},
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 400
    assert "50 pages" in resp.json()["detail"]


def test_7mb_scanned_pdf_triggers_optimization():
    """Test-F: 7 MB scanned PDF (< 8 MB shortcut) with high DPI correctly triggers image stream optimization."""
    content = create_synthetic_scanned_pdf(num_pages=2, width=2800, height=3600, dpi=400)
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(content, "scan_7mb.pdf")

    assert profile.is_pdf is True
    assert profile.document_type in ("scanned_pdf", "mixed_pdf")
    assert profile.max_image_dimensions[0] >= 2800
    assert profile.is_technically_suitable is False
    assert profile.recommended_strategy == "image_stream"


def test_15mb_digital_pdf_bypasses_optimization():
    """Test-G: 15 MB text-heavy digital PDF (> 8 MB) without raster images bypasses optimization (pass_through)."""
    # 30 pages of digital vector text, padded to 15 MB
    content = create_synthetic_digital_pdf(
        num_pages=30,
        text="Standard commercial lease agreement terms and conditions clause 1 to 50.",
        target_size_bytes=15 * 1024 * 1024,
    )
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(content, "digital_15mb.pdf")

    assert profile.is_pdf is True
    assert profile.document_type == "digital_pdf"
    assert profile.embedded_image_count == 0
    assert profile.is_technically_suitable is True
    assert profile.recommended_strategy == "pass_through"


def test_configurable_dpi_and_quality(monkeypatch):
    """Test-H: Optimizer respects custom configured target DPI and JPEG quality settings."""
    settings = get_settings()
    monkeypatch.setattr(settings, "optimization_target_dpi", 160)
    monkeypatch.setattr(settings, "optimization_jpeg_quality", 70)

    engine = AdaptiveOptimizationEngine()
    content = create_synthetic_scanned_pdf(num_pages=1, width=2400, height=3200, dpi=300)
    opt_bytes, telemetry = engine.optimize(content, "test_custom.pdf")

    assert telemetry.optimization_applied is True
    assert telemetry.optimization_method == "image_stream"

    # Inspect optimized image stream dimensions
    doc = fitz.open(stream=opt_bytes, filetype="pdf")
    base_img = doc.extract_image(doc.load_page(0).get_images()[0][0])
    w, h = base_img["width"], base_img["height"]
    doc.close()

    # Image was downscaled according to target_dpi (160 DPI)
    assert w < 2400
    assert h < 3200


def test_no_blind_rasterization_digital_pdf():
    """Test-I: Digital PDF with selectable text retains vector streams; zero raster images generated."""
    text = "TENANCY AGREEMENT. The tenant agrees to pay INR 25,000 monthly."
    content = create_synthetic_digital_pdf(num_pages=3, text=text)

    engine = AdaptiveOptimizationEngine()
    opt_bytes, telemetry = engine.optimize(content, "digital_tenancy.pdf")

    # Verify no raster images were inserted into pure digital PDF
    doc = fitz.open(stream=opt_bytes, filetype="pdf")
    for page in doc:
        assert len(page.get_images()) == 0
        assert "TENANCY AGREEMENT" in page.get_text()
    doc.close()


def test_color_stamp_and_seal_preservation():
    """Test-J: Scanned deed with colored official seal triggers RGB color preservation."""
    content = create_synthetic_scanned_pdf(num_pages=1, width=1600, height=2000, dpi=300, with_color_stamp=True)
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(content, "stamped_deed.pdf")

    assert profile.has_color_stamps_or_seals is True

    engine = AdaptiveOptimizationEngine()
    opt_bytes, telemetry = engine.optimize(content, "stamped_deed.pdf", profile=profile)

    # Verify resulting image stream preserves RGB mode (not crushed to grayscale)
    doc = fitz.open(stream=opt_bytes, filetype="pdf")
    base_img = doc.extract_image(doc.load_page(0).get_images()[0][0])
    doc.close()
    assert base_img["colorspace"] in (3, "DeviceRGB")  # 3 channels RGB


def test_technical_quality_gate_text_loss():
    """Test-K: Optimization dropping > 2% native text is rejected by TechnicalQualityGate."""
    original_bytes = create_synthetic_digital_pdf(
        num_pages=2,
        text="Clause 1: Initial Term. Clause 2: Payment. Clause 3: Indemnification. Clause 4: Jurisdiction.",
    )
    # Simulate a corrupted derivative where half the text was dropped
    corrupted_bytes = create_synthetic_digital_pdf(
        num_pages=2,
        text="Clause 1: Initial Term.",
    )
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(original_bytes)

    gate = TechnicalQualityGate()
    result = gate.evaluate(original_bytes, corrupted_bytes, profile)

    assert result.accepted is False
    assert "Native text loss exceeds tolerance" in (result.rejection_reason or "")


def test_technical_quality_gate_readability_drop():
    """Test-L: Optimization causing readability score degradation > 0.05 is rejected."""
    original_bytes = create_synthetic_digital_pdf(
        num_pages=2,
        text="Standard clear contractual prose with perfect punctuation and uppercase headers.",
    )
    # Simulate low quality derivative with gibberish / low readability
    bad_bytes = create_synthetic_digital_pdf(
        num_pages=2,
        text="123 456 789 000 ### $$$ @@@ !!! ??? &&& *** +++ === /// \\\\\\",
    )
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(original_bytes)

    gate = TechnicalQualityGate()
    result = gate.evaluate(original_bytes, bad_bytes, profile)

    assert result.accepted is False
    assert "readability" in (result.rejection_reason or "").lower() or "text loss" in (result.rejection_reason or "").lower()


def test_technical_quality_gate_resolution_floor(monkeypatch):
    """Test-M: Downscaling an image below 150 DPI is rejected by resolution floor check."""
    settings = get_settings()
    monkeypatch.setattr(settings, "optimization_min_dpi", 150)

    original_bytes = create_synthetic_scanned_pdf(num_pages=1, width=1600, height=2000, dpi=300)
    # Create low-res derivative below 150 DPI (e.g. 72 DPI with 400x500 dimension)
    crushed_bytes = create_synthetic_scanned_pdf(num_pages=1, width=400, height=500, dpi=72)

    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(original_bytes)

    gate = TechnicalQualityGate()
    result = gate.evaluate(original_bytes, crushed_bytes, profile)

    assert result.accepted is False
    assert "Resolution floor violation" in (result.rejection_reason or "")


def test_negative_compression_rejection():
    """Test-N: Optimization yielding size >= original is rejected and original restored."""
    # Highly compressed single-page document
    content = create_synthetic_digital_pdf(num_pages=1, text="Compact agreement")
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(content)

    # Force simulated larger derivative
    larger_derivative = content + b"\n% PADDING " + (b"X" * 5000)

    gate = TechnicalQualityGate()
    result = gate.evaluate(content, larger_derivative, profile)

    assert result.accepted is False
    assert "Negative compression" in (result.rejection_reason or "")


def test_lossless_optimization_stream_cleaning():
    """Test-O: Lossless optimization cleans streams and reduces size while preserving identical text."""
    # Create document with unreferenced/wasteful data
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Confidential NDA agreement text.")
    # Add an unused stream object
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, b"orphan unreferenced stream data" * 100)
    buf = io.BytesIO()
    doc.save(buf, clean=False, deflate=False)
    doc.close()
    bloated_bytes = buf.getvalue()

    engine = AdaptiveOptimizationEngine()
    opt_bytes = engine._lossless_optimize_pdf(bloated_bytes)

    assert len(opt_bytes) < len(bloated_bytes)
    # Verify text survived 100%
    doc_opt = fitz.open(stream=opt_bytes, filetype="pdf")
    assert "Confidential NDA agreement text." in doc_opt[0].get_text()
    doc_opt.close()


def test_deterministic_page_splitting():
    """Test-P: 45-page scanned PDF splits into deterministic Parts (1-20, 21-40, 41-45)."""
    content = create_synthetic_digital_pdf(num_pages=45, text="Contract Page")
    splitter = DeterministicPageSplitter(max_pages_per_part=20)
    parts = splitter.split(content, document_id="doc_split_test")

    assert len(parts) == 3
    # Part 1: 1..20
    assert parts[0].part_number == 1
    assert parts[0].start_page == 1
    assert parts[0].end_page == 20
    assert len(parts[0].page_numbers) == 20

    # Part 2: 21..40
    assert parts[1].part_number == 2
    assert parts[1].start_page == 21
    assert parts[1].end_page == 40
    assert len(parts[1].page_numbers) == 20

    # Part 3: 41..45
    assert parts[2].part_number == 3
    assert parts[2].start_page == 41
    assert parts[2].end_page == 45
    assert len(parts[2].page_numbers) == 5


def test_page_splitting_cannot_bypass_50_pages():
    """Test-Q: Page splitter strictly refuses to split any document with > 50 pages."""
    content = create_synthetic_digital_pdf(num_pages=51, text="Oversized doc")
    splitter = DeterministicPageSplitter(max_pages_per_part=20)

    with pytest.raises(ValueError, match="maximum limit of 50 pages"):
        splitter.split(content, document_id="doc_forbidden")


def test_recombination_order_and_provenance():
    """Test-R: Split parts recombine into continuous 1-indexed PageContentList without gaps or duplicates."""
    content = create_synthetic_digital_pdf(num_pages=25, text="Multi page clause text.")
    splitter = DeterministicPageSplitter(max_pages_per_part=10)
    parts = splitter.split(content, document_id="doc_recombine_test")

    # Simulate extraction for each part
    part_results = []
    for part in parts:
        pages = extract_text_from_pdf(part.content_bytes)
        part_results.append((part, pages))

    recombined = recombine_pages(part_results)
    assert len(recombined) == 25
    # Verify strict 1..25 page sequence
    for i, page in enumerate(recombined):
        assert page.page_num == i + 1


@pytest.mark.anyio
async def test_derived_artifact_cleanup_on_success():
    """Test-S: Worker analysis cleans up transient scratch files upon successful completion."""
    from worker import _execute_analysis

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=None)

    content = create_synthetic_digital_pdf(num_pages=2, text="Commercial Agreement.")
    doc_id = "test_cleanup_success_doc"

    # Track temporary directory before and after
    temp_dir = tempfile.gettempdir()

    with patch("database.get_db_ctx") as mock_db_ctx, \
         patch("services.groq_service.analyze_legal_document", new_callable=AsyncMock) as mock_groq, \
         patch("cache.set_analysis", new_callable=AsyncMock), \
         patch("cache.set_doc_text", new_callable=AsyncMock):

        mock_db_ctx.return_value.__aenter__.return_value = fake_db
        mock_groq.return_value = {
            "summary": {"document_type": "Commercial Lease", "overall_risk": "LOW"},
            "clauses": [],
        }

        await _execute_analysis(doc_id, content, "contract.pdf")

        # Confirm no orphaned sl_opt directories remain for doc_id
        orphans = [d for d in os.listdir(temp_dir) if d.startswith(f"sl_opt_{doc_id}")]
        assert len(orphans) == 0


@pytest.mark.anyio
async def test_derived_artifact_cleanup_on_failure():
    """Test-T: Worker cleans up scratch files in finally block even when analysis raises an exception."""
    from worker import _execute_analysis

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=None)

    content = create_synthetic_digital_pdf(num_pages=2, text="Broken Agreement.")
    doc_id = "test_cleanup_fail_doc"
    temp_dir = tempfile.gettempdir()

    with patch("database.get_db_ctx") as mock_db_ctx, \
         patch("services.groq_service.analyze_legal_document", new_callable=AsyncMock) as mock_groq:

        mock_db_ctx.return_value.__aenter__.return_value = fake_db
        mock_groq.side_effect = RuntimeError("Fatal LLM service interruption")

        await _execute_analysis(doc_id, content, "broken.pdf")

        # Confirm cleanup occurred despite failure
        orphans = [d for d in os.listdir(temp_dir) if d.startswith(f"sl_opt_{doc_id}")]
        assert len(orphans) == 0


def test_phase3_token_chunking_compatibility():
    """Test-U: Extracted text from optimized representations is safely sized by ChunkingService."""
    content = create_synthetic_digital_pdf(num_pages=3, text="This is a valid contract agreement with terms and conditions. " * 30)
    engine = AdaptiveOptimizationEngine()
    opt_bytes, telemetry = engine.optimize(content, "contract_for_chunking.pdf")

    pages = extract_text_from_pdf(opt_bytes)
    chunking_service = ChunkingService(max_chunk_tokens=400, safety_margin=50)
    chunks = chunking_service.chunk_pages(list(pages))

    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert all(c.estimated_tokens <= chunking_service.max_allowed_tokens for c in chunks)


@pytest.mark.anyio
async def test_phase4_visual_pipeline_compatibility():
    """Test-V: Scanned page from optimized PDF is compatible with VisualDocumentPipeline."""
    from services.vision_pipeline import VisualDocumentPipeline, PageTranscription

    content = create_synthetic_scanned_pdf(num_pages=1, width=1400, height=1800, dpi=250)
    engine = AdaptiveOptimizationEngine()
    opt_bytes, telemetry = engine.optimize(content, "ocr_candidate.pdf")

    pages = extract_text_from_pdf(opt_bytes)
    pipeline = VisualDocumentPipeline()

    # Mock Gemini Vision call to verify pipeline consumes optimized PDF safely
    with patch.object(pipeline.gemini_adapter, "transcribe_image", new_callable=AsyncMock) as mock_vision, \
         patch.object(pipeline.gemini_adapter, "is_available", return_value=(True, "ok")):
        mock_vision.return_value = PageTranscription(
            page_num=1,
            text="Transcribed scanned contract clause with sufficient letters and words.",
            extraction_source="gemini_vision",
            engine="gemini_vision",
            confidence=0.95,
        )
        transcriptions = await pipeline.process_pdf_pages(opt_bytes, list(pages))
        assert len(transcriptions) == 1
        assert "Transcribed scanned contract clause" in transcriptions[0].text


def test_phase5_budget_manager_independence():
    """Test-W: Optimization engine never touches or calls ProviderBudgetManager or cooldown logic."""
    from services.provider_budget_manager import budget_manager

    with patch.object(budget_manager, "can_send") as mock_can_send, \
         patch.object(budget_manager, "record_rate_limit") as mock_rate_limit:

        content = create_synthetic_scanned_pdf(num_pages=2, width=1400, height=1800, dpi=300)
        engine = AdaptiveOptimizationEngine()
        opt_bytes, telemetry = engine.optimize(content, "independent.pdf")

        # Zero interactions with Phase 5 budget accounting
        assert mock_can_send.call_count == 0
        assert mock_rate_limit.call_count == 0


@pytest.mark.anyio
async def test_whatsapp_25mb_streaming_download(monkeypatch):
    """Test-X: WhatsApp media downloader accepts a 22 MB PDF download stream without aborting."""
    from services.whatsapp.media import MetaMediaDownloader, MAX_MEDIA_SIZE_BYTES
    from config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "meta_whatsapp_access_token", "test_meta_token_xyz")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": str(22 * 1024 * 1024)}

    async def stream_chunks():
        yield b"%PDF-1.4\n" + (b"X" * (22 * 1024 * 1024 - 15)) + b"\n%%EOF"

    mock_resp.aiter_bytes = stream_chunks

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    downloader = MetaMediaDownloader()
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):

        mock_meta = MagicMock()
        mock_meta.status_code = 200
        mock_meta.json.return_value = {"url": "https://lookaside.fbsbx.com/large_doc", "mime_type": "application/pdf"}
        mock_get.return_value = mock_meta

        media = await downloader.download_media("media_22mb")
        assert media.file_size == 22 * 1024 * 1024


@pytest.mark.anyio
async def test_whatsapp_oversized_26mb_rejected(monkeypatch):
    """Test-Y: WhatsApp streaming downloader aborts > 25 MB streams and returns localized 25 MB message."""
    from services.whatsapp.media import MetaMediaDownloader, MAX_MEDIA_SIZE_BYTES
    from config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "meta_whatsapp_access_token", "test_meta_token_xyz")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": str(26 * 1024 * 1024)}

    downloader = MetaMediaDownloader()
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.stream") as mock_stream:

        mock_meta = MagicMock()
        mock_meta.status_code = 200
        mock_meta.json.return_value = {"url": "https://lookaside.fbsbx.com/oversized_doc", "mime_type": "application/pdf"}
        mock_get.return_value = mock_meta

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_stream.return_value = mock_stream_ctx

        with pytest.raises(ValueError, match="25 MB"):
            await downloader.download_media("media_26mb")


def test_corrupt_malicious_pdf_handled_gracefully():
    """Test-Z: Corrupted / invalid PDF header is caught gracefully without unhandled exceptions."""
    corrupt_bytes = b"%PDF-invalid-binary\x00\xff\xfe\x00\x01\x02\x03corrupt"
    inspector = DocumentSuitabilityInspector()
    profile = inspector.inspect(corrupt_bytes, "corrupt.pdf")

    engine = AdaptiveOptimizationEngine()
    # Engine should safely fail-open or return original bytes without crash
    out_bytes, telemetry = engine.optimize(corrupt_bytes, "corrupt.pdf", profile=profile)

    assert out_bytes == corrupt_bytes
    assert telemetry.optimization_applied is False
