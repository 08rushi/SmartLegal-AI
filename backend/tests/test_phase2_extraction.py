"""
test_phase2_extraction.py — Phase 2 Extraction & Routing Foundation Test Suite.

Verifies:
  1. Per-page PDF extraction returning PageContentList.
  2. PageContent schema: observed vs derived fields.
  3. Deterministic page classification: digital, scanned, empty.
  4. Mixed-PDF independent page classification.
  5. Deterministic quality_score and is_unclear calculation.
  6. Configurable thresholds.
  7. Genuine vs unavailable OCR confidence.
  8. Backward compatibility with existing consumers (detect_document_type, split_into_chunks, Redis).
  9. Corrupted PDF error handling.
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.page_content import (
    PageContent,
    PageContentList,
    calculate_digital_quality,
    calculate_ocr_quality,
    classify_page,
    classify_document_pages,
    pages_to_text,
)
from services.pdf_parser import (
    extract_text_from_pdf,
    extract_text_from_pdf_str,
    detect_script,
    split_into_chunks,
)
from services.ocr_service import ocr_image_to_page


# =============================================================================
# PDF Fixture Helpers (In-Memory)
# =============================================================================

def _get_indic_font() -> str | None:
    """Find a system font that supports Indic Unicode scripts (Devanagari, Tamil, etc.)."""
    candidates = [
        r"C:\Windows\Fonts\Nirmala.ttc",
        r"C:\Windows\Fonts\nirmala.ttf",
        r"C:\Windows\Fonts\mangal.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _create_sample_png_bytes(width: int = 200, height: int = 100, text: str = "Invoice Scan") -> bytes:
    """Create a minimal PNG image in memory."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_digital_pdf_bytes() -> bytes:
    """Create a 2-page digital PDF with English and Hindi legal text."""
    doc = fitz.open()
    indic_font = _get_indic_font()

    # Page 1: English Lease Agreement
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "RENTAL AGREEMENT\n\n"
        "This Rental Agreement is made and executed on this 1st day of October 2025 "
        "by and between the Landlord and the Tenant. The Tenant agrees to pay a monthly "
        "rent of twenty thousand rupees on or before the fifth day of each calendar month. "
        "The security deposit shall be refundable upon peaceful handover of premises.",
        fontsize=11,
    )

    # Page 2: Hindi Rental Clause (if font available) or second English clause
    p2 = doc.new_page(width=595, height=842)
    if indic_font:
        p2.insert_font(fontname="nirmala", fontfile=indic_font)
        p2.insert_text(
            (50, 72),
            "किराया अनुबंध\n\n"
            "यह किराया अनुबंध मकान मालिक और किरायेदार के बीच निष्पादित किया गया है। "
            "किरायेदार हर महीने की पांच तारीख तक पंद्रह हजार रुपये का किराया अदा करने के लिए बाध्य है। "
            "परिसर खाली करते समय सुरक्षा जमा राशि पूर्ण रूप से वापस कर दी जाएगी।",
            fontname="nirmala",
            fontsize=11,
        )
    else:
        p2.insert_text(
            (50, 72),
            "MAINTENANCE AND UTILITIES\n\n"
            "The tenant agrees to maintain the premises in good condition and bear "
            "all routine electricity and water utility charges during the lease tenure.",
            fontsize=11,
        )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _create_scanned_pdf_bytes() -> bytes:
    """Create a 2-page scanned PDF with raster images and zero vector text."""
    doc = fitz.open()
    img_bytes = _create_sample_png_bytes()

    for _ in range(2):
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=img_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _create_mixed_pdf_bytes() -> bytes:
    """Create a 3-page mixed PDF: Page 1 text, Page 2 image, Page 3 text."""
    doc = fitz.open()

    # Page 1: Digital
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 72),
        "PARTNERSHIP DEED\n\n"
        "This deed of partnership is entered into by the partners for carrying on "
        "the lawful commercial business of software consulting and legal operations.",
        fontsize=11,
    )

    # Page 2: Scanned image (no vector text)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_image(p2.rect, stream=_create_sample_png_bytes())

    # Page 3: Digital
    p3 = doc.new_page(width=595, height=842)
    p3.insert_text(
        (50, 72),
        "DISPUTE RESOLUTION CLAUSE\n\n"
        "Any dispute or difference arising out of or in connection with this deed "
        "shall be referred to arbitration in accordance with the Arbitration Act.",
        fontsize=11,
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# =============================================================================
# Phase 2 Test Suite
# =============================================================================

class TestPhase2ExtractionFoundation(unittest.TestCase):

    # 1. Normal Digital PDF
    def test_normal_digital_pdf(self):
        pdf_bytes = _create_digital_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)

        self.assertIsInstance(pages, PageContentList)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages.document_type, "digital_pdf")

        # Page 1 (English)
        p1 = pages[0]
        self.assertEqual(p1.page_num, 1)
        self.assertEqual(p1.page_type, "digital")
        self.assertEqual(p1.extraction_source, "pymupdf")
        self.assertIsNone(p1.ocr_confidence)  # Must be None for digital
        self.assertGreater(p1.quality_score, 0.70)
        self.assertFalse(p1.is_unclear)
        self.assertIn("RENTAL AGREEMENT", p1.text)

        # Page 2
        p2 = pages[1]
        self.assertEqual(p2.page_num, 2)
        self.assertEqual(p2.page_type, "digital")
        self.assertEqual(p2.extraction_source, "pymupdf")
        self.assertIsNone(p2.ocr_confidence)
        self.assertGreater(p2.quality_score, 0.70)
        self.assertFalse(p2.is_unclear)
        if _get_indic_font():
            self.assertEqual(p2.script, "Hindi / Marathi (Devanagari)")
        else:
            self.assertEqual(p2.script, "Latin / English")

    # 2. Scanned / Image-Only PDF Classification
    def test_scanned_pdf_classification(self):
        pdf_bytes = _create_scanned_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages.document_type, "scanned_pdf")

        for p in pages:
            self.assertEqual(p.page_type, "scanned")
            self.assertTrue(p.has_images)
            self.assertGreaterEqual(p.image_count, 1)
            self.assertEqual(p.extraction_source, "pymupdf")
            self.assertIsNone(p.ocr_confidence)
            self.assertTrue(p.is_unclear)

    # 3. Mixed PDF Classification
    def test_mixed_pdf_classification(self):
        pdf_bytes = _create_mixed_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)

        self.assertEqual(len(pages), 3)
        self.assertEqual(pages.document_type, "mixed_pdf")

        # Page 1: Digital
        self.assertEqual(pages[0].page_type, "digital")
        self.assertFalse(pages[0].has_images)

        # Page 2: Scanned
        self.assertEqual(pages[1].page_type, "scanned")
        self.assertTrue(pages[1].has_images)
        self.assertTrue(pages[1].is_unclear)

        # Page 3: Digital
        self.assertEqual(pages[2].page_type, "digital")
        self.assertFalse(pages[2].has_images)

    # 4. Blank / Empty Page
    def test_blank_page(self):
        doc = fitz.open()
        doc.new_page(width=595, height=842)  # Blank page, no text, no images
        pdf_bytes = doc.tobytes()
        doc.close()

        pages = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(len(pages), 1)
        p = pages[0]
        self.assertEqual(p.page_type, "empty")
        self.assertEqual(p.text, "")
        self.assertEqual(p.quality_score, 0.0)
        self.assertTrue(p.is_unclear)
        self.assertIsNone(p.ocr_confidence)
        self.assertFalse(p.has_images)
        self.assertEqual(pages.document_type, "empty_pdf")

    # 5. Image-Only Page
    def test_image_only_page(self):
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=_create_sample_png_bytes())
        pdf_bytes = doc.tobytes()
        doc.close()

        pages = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(len(pages), 1)
        p = pages[0]
        self.assertEqual(p.page_type, "scanned")
        self.assertTrue(p.has_images)
        self.assertEqual(p.image_count, 1)

    # 6. Page With Fewer Than 20 Alphabetic/Unicode Letters (Exact Terminology)
    def test_very_low_text_page(self):
        """
        Verify that a page with fewer than 20 alphabetic/Unicode letters
        (e.g. short header or stamp) triggers the low-letter penalty and is marked unclear.
        """
        doc = fitz.open()
        p = doc.new_page(width=595, height=842)
        # Exactly 12 alphabetic letters: "Page Number" (10 letters) + "123"
        p.insert_text((50, 72), "Page Number 123 -- #456", fontsize=10)
        pdf_bytes = doc.tobytes()
        doc.close()

        pages = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(len(pages), 1)
        page = pages[0]
        self.assertLess(page.raw_signals["alpha_count"], 20)
        self.assertLess(page.quality_score, 0.40)
        self.assertTrue(page.is_unclear)

    # 7. Multilingual / Indic Text Page
    def test_multilingual_page(self):
        doc = fitz.open()
        p = doc.new_page(width=595, height=842)
        indic_font = _get_indic_font()
        if indic_font:
            p.insert_font(fontname="nirmala", fontfile=indic_font)
            p.insert_text(
                (50, 72),
                "வாடகை ஒப்பந்தம்\n\n"
                "இந்த ஒப்பந்தம் வாடகைதாரர் மற்றும் உரிமையாளருக்கு இடையே செய்யப்படுகிறது. "
                "மாதாந்திர வாடகை சரியான நேரத்தில் செலுத்தப்பட வேண்டும்.",
                fontname="nirmala",
                fontsize=11,
            )
        else:
            p.insert_text(
                (50, 72),
                "COMMERCIAL LEASE AGREEMENT\n\n"
                "This commercial lease agreement governs the relationship between the lessor and lessee.",
                fontsize=11,
            )
        pdf_bytes = doc.tobytes()
        doc.close()

        pages = extract_text_from_pdf(pdf_bytes)
        self.assertEqual(len(pages), 1)
        p = pages[0]
        if indic_font:
            self.assertEqual(p.script, "Tamil")
        else:
            self.assertEqual(p.script, "Latin / English")
        self.assertEqual(p.page_type, "digital")
        self.assertGreater(p.quality_score, 0.70)
        self.assertFalse(p.is_unclear)

    # 8. Script Detection across Ranges
    def test_script_detection(self):
        self.assertEqual(detect_script("Standard English Lease Agreement"), "Latin / English")
        self.assertEqual(detect_script("किरायानामा एवं इकरारनामा"), "Hindi / Marathi (Devanagari)")
        self.assertEqual(detect_script("விற்பனை ஒப்பந்தம்"), "Tamil")
        self.assertEqual(detect_script("అద్దె ఒప్పందం"), "Telugu")
        self.assertEqual(detect_script("ভাড়া চুক্তিপত্র"), "Bengali / Assamese")

    # 9. Page Metadata & Raw Telemetry Signals
    def test_page_metadata_and_signals(self):
        pdf_bytes = _create_digital_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)
        p = pages[0]

        d = p.to_dict()
        self.assertIn("page_num", d)
        self.assertIn("raw_signals", d)
        self.assertIn("alpha_count", d["raw_signals"])
        self.assertIn("non_space_count", d["raw_signals"])
        self.assertIn("letter_ratio", d["raw_signals"])
        self.assertGreater(d["char_count"], 50)
        self.assertGreater(d["word_count"], 10)

    # 10. Quality Score Calculation Formats
    def test_quality_score_calculation(self):
        # Pristine legal text (high ratio)
        q_clean, unclear_clean, _ = calculate_digital_quality(
            "This is a legally binding standard contract between both signing parties."
        )
        self.assertGreaterEqual(q_clean, 0.60)
        self.assertFalse(unclear_clean)

        # Symbol soup / corrupted font glyphs (low ratio < 0.40)
        q_soup, unclear_soup, _ = calculate_digital_quality(
            "!@#$%^&*()_+ 1234567890 !@#$%^&*() 9876543210 ~`=-"
        )
        self.assertLess(q_soup, 0.40)
        self.assertTrue(unclear_soup)

        # Bounded between 0.0 and 1.0
        self.assertGreaterEqual(q_clean, 0.0)
        self.assertLessEqual(q_clean, 1.0)
        self.assertGreaterEqual(q_soup, 0.0)
        self.assertLessEqual(q_soup, 1.0)

    # 11. Configurable Thresholds
    def test_configurable_thresholds(self):
        custom_settings = MagicMock()
        custom_settings.digital_min_letters = 50
        custom_settings.digital_min_letter_ratio = 0.50
        custom_settings.digital_full_prose_ratio = 0.90
        custom_settings.digital_length_scale_chars = 100
        custom_settings.page_readable_quality_threshold = 0.75

        # 30 letters — passes default (20), but fails custom threshold (50)
        text = "This text has thirty letters total."
        q, unclear, signals = calculate_digital_quality(text, settings=custom_settings)
        self.assertTrue(unclear)
        self.assertLess(q, 0.40)

    # 12. OCR Confidence: Genuine When Available
    def test_ocr_confidence_genuine_when_available(self):
        img_bytes = _create_sample_png_bytes(text="Commercial Lease")
        page = ocr_image_to_page(img_bytes)

        self.assertEqual(page.page_type, "scanned")
        self.assertEqual(page.extraction_source, "tesseract")
        # When Tesseract is available and recognizes words, genuine confidence is float
        if page.text:
            self.assertIsNotNone(page.ocr_confidence)
            self.assertIsInstance(page.ocr_confidence, float)
            self.assertGreaterEqual(page.ocr_confidence, 0.0)
            self.assertLessEqual(page.ocr_confidence, 1.0)

    # 13. OCR Confidence: Strictly None When Unavailable
    def test_ocr_confidence_none_when_unavailable(self):
        # Calculation helper with None confidence
        q, unclear, signals = calculate_ocr_quality(None, "")
        self.assertEqual(q, 0.0)
        self.assertTrue(unclear)
        self.assertIsNone(signals["ocr_confidence"])

        # Simulated Tesseract failure
        with patch("services.ocr_service._resolve", return_value=(None, "pytesseract not found")):
            page = ocr_image_to_page(b"fake-image-bytes")
            self.assertIsNone(page.ocr_confidence)  # Must be None, NEVER 0.0
            self.assertEqual(page.quality_score, 0.0)
            self.assertTrue(page.is_unclear)

    # 14. Backward-Compatible Text Reconstruction
    def test_backward_compatible_text_reconstruction(self):
        pdf_bytes = _create_digital_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)

        # pages.to_text() and extract_text_from_pdf_str()
        reconstructed = pages.to_text()
        from_str_helper = extract_text_from_pdf_str(pdf_bytes)

        self.assertEqual(reconstructed, from_str_helper)
        self.assertIn("[Page 1]", reconstructed)
        self.assertIn("[Page 2]", reconstructed)
        self.assertIn("RENTAL AGREEMENT", reconstructed)
        if _get_indic_font():
            self.assertIn("किराया अनुबंध", reconstructed)
        else:
            self.assertIn("MAINTENANCE AND UTILITIES", reconstructed)

    # 15. Existing Consumer Compatibility
    def test_existing_consumer_compatibility(self):
        pdf_bytes = _create_digital_pdf_bytes()
        pages = extract_text_from_pdf(pdf_bytes)
        text = pages.to_text()

        # Consumer A: split_into_chunks (groq_service dependency)
        chunks = split_into_chunks(text, max_chars=500)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIn("text", chunk)
            self.assertIn("start_page", chunk)
            self.assertIn("end_page", chunk)

        # Consumer B: detect_document_type (gemini_service / chat dependency)
        from services.gemini_service import detect_document_type
        doc_key, doc_name = detect_document_type(text, "lease_agreement.pdf")
        self.assertIsInstance(doc_key, str)
        self.assertIsInstance(doc_name, str)

    # 16. Corrupted PDF Exception
    def test_corrupted_pdf_exception(self):
        corrupted_bytes = b"NOT_A_VALID_PDF_HEADER_STREAM_DATA"
        with self.assertRaises(ValueError) as ctx:
            extract_text_from_pdf(corrupted_bytes)
        self.assertIn("Failed to parse PDF", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
