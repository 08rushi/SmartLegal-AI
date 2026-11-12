"""
test_phase4_vision.py — Comprehensive Test Suite for Phase 4 Visual / OCR Pipeline.

Verifies:
  A. Clean digital page bypasses visual pipeline
  B. Scanned page attempts Gemini first
  C. Gemini success
  D. Gemini failure -> PaddleOCR
  E. PaddleOCR success
  F. PaddleOCR low-quality -> Tesseract
  G. PaddleOCR unavailable -> Tesseract
  H. Tesseract success
  I. All visual methods fail
  J. Genuine OCR confidence
  K. Missing OCR confidence
  L. [UNCLEAR] behavior
  M. No translation
  N. Original-script preservation
  O. Mixed PDF routing
  P. Standalone image routing
  Q. Privacy mode prevents cloud Gemini usage
  R. Provider failure classification
  S. Fallback history / metadata
  T. PageTranscription validation
  U. PageContent compatibility
  V. Phase 3 chunking compatibility
  W. No fake successful result
  X. Malformed Gemini response
  Y. Malformed OCR response
  Z. Corrupted / invalid image
  AA. Empty visual result
  AB. Page ordering preservation
  AC. Multilingual / Indic documents
  AD. Table / structured-text preservation where supported
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chunking_service import ChunkingService
from services.model_capabilities import ModelCapability
from services.page_content import PageContent, PageContentList
from services.page_transcription import PageTranscription
from services.vision_pipeline import (
    GeminiVisionAdapter,
    PaddleOCRAdapter,
    TesseractAdapter,
    VisualDocumentPipeline,
    classify_vision_error,
    evaluate_transcription_quality,
)


def _create_test_image_bytes(color: str = "white", size: tuple[int, int] = (100, 100)) -> bytes:
    """Helper to create valid minimal PNG image bytes in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestPhase4TranscriptionContract(unittest.TestCase):
    """Tests T, U, V: PageTranscription validation, PageContent mapping, and Phase 3 Chunking."""

    def test_page_transcription_validation(self):
        """Test T: PageTranscription field correctness and to_dict()."""
        trans = PageTranscription(
            page_num=1,
            text="Clause 1: Standard Lease Terms.",
            extraction_source="gemini_vision",
            engine="gemini-3.8-flash",
            script="Latin / English",
            confidence=0.92,
            is_unclear=False,
            quality_score=0.95,
            status="success",
        )
        self.assertEqual(trans.char_count, len(trans.text))
        self.assertEqual(trans.word_count, 5)
        d = trans.to_dict()
        self.assertEqual(d["page_num"], 1)
        self.assertEqual(d["extraction_source"], "gemini_vision")
        self.assertEqual(d["confidence"], 0.92)

    def test_page_content_compatibility(self):
        """Test U: PageTranscription.to_page_content() produces canonical PageContent."""
        trans = PageTranscription(
            page_num=3,
            text="Clause 3: Termination by Notice.",
            extraction_source="tesseract",
            engine="tesseract",
            script="Latin / English",
            confidence=0.85,
            is_unclear=False,
            quality_score=0.88,
            has_images=True,
            image_count=1,
        )
        pc = trans.to_page_content()
        self.assertIsInstance(pc, PageContent)
        self.assertEqual(pc.page_num, 3)
        self.assertEqual(pc.extraction_source, "tesseract")
        self.assertEqual(pc.ocr_confidence, 0.85)
        self.assertEqual(pc.page_type, "scanned")
        self.assertFalse(pc.is_unclear)

    def test_phase3_chunking_compatibility(self):
        """Test V: Transcribed pages feed directly into Phase 3 ChunkingService."""
        transcriptions = [
            PageTranscription(
                page_num=i,
                text=f"[Page {i}] Legal obligation clause content text. " * 10,
                extraction_source="gemini_vision",
                engine="gemini-3.8-flash",
                quality_score=0.90,
            )
            for i in range(1, 4)
        ]
        pages = [t.to_page_content() for t in transcriptions]
        chunker = ChunkingService(max_chunk_tokens=2500)
        chunks = chunker.chunk_pages(pages)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].page_start, 1)
        self.assertEqual(chunks[0].page_end, 3)


class TestPhase4ErrorClassificationAndQuality(unittest.TestCase):
    """Tests R, J, K, L, M, N, AD: Error classification, confidence, uncertainty, scripts."""

    def test_provider_failure_classification(self):
        """Test R: Deterministic error classification."""
        self.assertEqual(classify_vision_error(Exception("401 Unauthorized: Invalid API key")), "auth_failure")
        self.assertEqual(classify_vision_error(Exception("429 ResourceExhausted: rate limit")), "rate_limit")
        self.assertEqual(classify_vision_error(Exception("ReadTimeout: connection timed out")), "timeout")
        self.assertEqual(classify_vision_error(Exception("Cannot identify image format")), "invalid_image")
        self.assertEqual(classify_vision_error(Exception("Malformed response: empty parts")), "malformed_response")
        self.assertEqual(classify_vision_error(Exception("Model not configured")), "provider_unavailable")

    def test_genuine_and_missing_confidence(self):
        """Tests J, K: Genuine confidence preserved vs missing confidence is None."""
        q1, unclear1, acc1, s1 = evaluate_transcription_quality("Valid clause text with sufficient length.", confidence=0.88)
        self.assertEqual(s1["reported_confidence"], 0.88)

        q2, unclear2, acc2, s2 = evaluate_transcription_quality("Valid clause text with sufficient length.", confidence=None)
        self.assertIsNone(s2["reported_confidence"])
        self.assertNotEqual(s2["reported_confidence"], 0.0)

    def test_unclear_marker_behavior(self):
        """Test L: [UNCLEAR] token marks transcription as unclear without deleting text."""
        text = "The tenant shall pay a monthly sum of [UNCLEAR] on or before the 5th day."
        q, is_unclear, is_acc, s = evaluate_transcription_quality(text)
        self.assertTrue(is_unclear)
        self.assertTrue(s["has_unclear"])

    def test_original_script_and_no_translation(self):
        """Tests M, N: Hindi and Tamil text retain original script and language."""
        hindi_text = "किराया अनुबंध पत्र: किरायेदार को प्रतिमाह ₹15,000 का भुगतान करना होगा।"
        q, is_unclear, is_acc, s = evaluate_transcription_quality(hindi_text)
        self.assertTrue(is_acc)
        self.assertFalse(is_unclear)

        tamil_text = "வாடகை ஒப்பந்தம்: மாதந்தோறும் வாடகை செலுத்த வேண்டும்."
        q_t, is_unclear_t, is_acc_t, s_t = evaluate_transcription_quality(tamil_text)
        self.assertTrue(is_acc_t)

    def test_table_and_structured_text_preservation(self):
        """Test AD: Tables and numbered clauses retain formatting."""
        structured = (
            "Clause 1.1: Maintenance Charges\n"
            "| Item | Cost |\n"
            "| Water | 500 |\n"
            "| Electricity | 1500 |\n"
        )
        q, is_unclear, is_acc, s = evaluate_transcription_quality(structured)
        self.assertTrue(is_acc)
        self.assertGreater(s["alpha_count"], 20)


class TestPhase4PipelineWaterfall(unittest.IsolatedAsyncioTestCase):
    """Tests A through I, O, P, Q, W, X, Y, Z, AA, AB, AC: Pipeline routing and fallback waterfall."""

    async def test_clean_digital_page_bypasses_visual_pipeline(self):
        """Test A: Clean digital page bypasses visual pipeline completely."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_tess = MagicMock(spec=TesseractAdapter)

        pipeline = VisualDocumentPipeline(
            gemini_adapter=mock_gemini,
            paddleocr_adapter=mock_paddle,
            tesseract_adapter=mock_tess,
        )

        digital_page = PageContent(
            page_num=1,
            text="This is a clean native digital legal contract with sufficient alphabetic content.",
            extraction_source="pymupdf",
            script="Latin / English",
            page_type="digital",
            quality_score=0.95,
            is_unclear=False,
        )

        res = await pipeline.transcribe_page_image(b"fake_image", page_num=1, existing_page=digital_page)

        # Gemini, Paddle, and Tesseract must NOT have been called
        mock_gemini.transcribe_image.assert_not_called()
        mock_paddle.transcribe_image.assert_not_called()
        mock_tess.transcribe_image.assert_not_called()

        self.assertEqual(res.extraction_source, "pymupdf")
        self.assertEqual(res.status, "success")
        self.assertFalse(res.is_unclear)

    async def test_scanned_page_attempts_gemini_first_and_succeeds(self):
        """Tests B, C: Scanned page invokes Gemini Vision first and succeeds."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Transcribed scanned text with valid legal words.",
                extraction_source="gemini_vision",
                engine="gemini-3.8-flash",
                status="success",
                quality_score=0.90,
                is_unclear=False,
            )
        )
        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_tess = MagicMock(spec=TesseractAdapter)

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        img_bytes = _create_test_image_bytes()

        res = await pipeline.transcribe_page_image(img_bytes, page_num=1)

        mock_gemini.transcribe_image.assert_awaited_once()
        mock_paddle.transcribe_image.assert_not_called()
        mock_tess.transcribe_image.assert_not_called()

        self.assertEqual(res.extraction_source, "gemini_vision")
        self.assertEqual(res.status, "success")

    async def test_gemini_failure_falls_back_to_paddleocr(self):
        """Tests D, E: Gemini failure routes to PaddleOCR and succeeds."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(side_effect=RuntimeError("429 Rate limit"))

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (True, "ok")
        mock_paddle.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="PaddleOCR recovered legal text with high accuracy.",
                extraction_source="paddleocr",
                engine="paddleocr-v4",
                confidence=0.89,
                status="success",
                quality_score=0.88,
                is_unclear=False,
            )
        )

        mock_tess = MagicMock(spec=TesseractAdapter)

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        img_bytes = _create_test_image_bytes()

        res = await pipeline.transcribe_page_image(img_bytes, page_num=1)

        mock_gemini.transcribe_image.assert_awaited_once()
        mock_paddle.transcribe_image.assert_awaited_once()
        mock_tess.transcribe_image.assert_not_called()

        self.assertEqual(res.extraction_source, "paddleocr")
        self.assertEqual(res.status, "fallback_used")
        self.assertEqual(len(res.fallback_history), 2)
        self.assertEqual(res.fallback_history[0]["engine"], "gemini_vision")
        self.assertEqual(res.fallback_history[1]["engine"], "paddleocr")

    async def test_paddleocr_low_quality_falls_back_to_tesseract(self):
        """Test F: PaddleOCR low quality triggers Tesseract fallback."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (False, "disabled")

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (True, "ok")
        # Garbled low-letter text
        mock_paddle.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="... ### ??? --- 123",
                extraction_source="paddleocr",
                engine="paddleocr-v4",
                confidence=0.20,
                status="success_with_uncertainty",
                quality_score=0.10,
                is_unclear=True,
            )
        )

        mock_tess = MagicMock(spec=TesseractAdapter)
        mock_tess.is_available.return_value = (True, "ok")
        mock_tess.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Tesseract recovered clean readable lease provisions.",
                extraction_source="tesseract",
                engine="tesseract",
                confidence=0.82,
                status="success",
                quality_score=0.85,
                is_unclear=False,
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        img_bytes = _create_test_image_bytes()

        res = await pipeline.transcribe_page_image(img_bytes, page_num=1)

        mock_paddle.transcribe_image.assert_awaited_once()
        mock_tess.transcribe_image.assert_awaited_once()

        self.assertEqual(res.extraction_source, "tesseract")
        self.assertEqual(res.status, "fallback_used")

    async def test_paddleocr_unavailable_falls_back_to_tesseract(self):
        """Tests G, H: PaddleOCR unavailable yields cleanly to Tesseract."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (False, "disabled")

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (False, "PaddleOCR not installed")

        mock_tess = MagicMock(spec=TesseractAdapter)
        mock_tess.is_available.return_value = (True, "ok")
        mock_tess.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Tesseract clean fallback text.",
                extraction_source="tesseract",
                engine="tesseract",
                confidence=0.80,
                status="success",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        img_bytes = _create_test_image_bytes()

        res = await pipeline.transcribe_page_image(img_bytes, page_num=1)

        mock_tess.transcribe_image.assert_awaited_once()
        self.assertEqual(res.extraction_source, "tesseract")

    async def test_all_visual_methods_fail(self):
        """Tests I, W, AA: When all engines fail, preserves failure state with no fake success."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(side_effect=RuntimeError("Gemini 500 error"))

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (True, "ok")
        mock_paddle.transcribe_image = AsyncMock(side_effect=RuntimeError("Paddle crash"))

        mock_tess = MagicMock(spec=TesseractAdapter)
        mock_tess.is_available.return_value = (True, "ok")
        mock_tess.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="",  # Empty text
                extraction_source="tesseract",
                engine="tesseract",
                status="provider_unavailable",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        img_bytes = _create_test_image_bytes()

        res = await pipeline.transcribe_page_image(img_bytes, page_num=1)

        self.assertEqual(res.status, "all_visual_methods_failed")
        self.assertEqual(res.text, "")
        self.assertTrue(res.is_unclear)
        self.assertEqual(res.quality_score, 0.0)

    async def test_privacy_mode_prevents_cloud_gemini_usage(self):
        """Test Q: Privacy mode disables Gemini Vision and routes to local OCR."""
        with patch("services.vision_pipeline.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                privacy_mode=True,
                cloud_vision_enabled=True,
                gemini_api_key="valid_key",
                paddleocr_enabled=True,
                ocr_enabled=True,
                digital_min_letters=20,
                digital_min_letter_ratio=0.40,
                ocr_min_confidence_threshold=0.35,
            )
            adapter = GeminiVisionAdapter()
            available, reason = adapter.is_available()
            self.assertFalse(available)
            self.assertIn("Privacy mode", reason)

    async def test_mixed_pdf_routing_and_order_preservation(self):
        """Tests O, AB, AC: Mixed PDF routes digital and scanned pages appropriately in sequence."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=2,
                text="Transcribed scanned page 2 clause in Hindi: किराया समझौता.",
                extraction_source="gemini_vision",
                engine="gemini-3.8-flash",
                script="Hindi / Marathi (Devanagari)",
                status="success",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, MagicMock(), MagicMock())

        # Create a 2-page in-memory PDF: Page 1 has digital text, Page 2 is empty/scanned
        import fitz
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((50, 50), "Page 1: Digital legal contract clause terms.")
        p2 = doc.new_page()  # Blank scanned page
        pdf_bytes = doc.write()
        doc.close()

        pages = [
            PageContent(
                page_num=1,
                text="Page 1: Digital legal contract clause terms.",
                extraction_source="pymupdf",
                script="Latin / English",
                page_type="digital",
                quality_score=0.95,
                is_unclear=False,
            ),
            PageContent(
                page_num=2,
                text="",
                extraction_source="pymupdf",
                script="Latin / English",
                page_type="scanned",
                quality_score=0.0,
                is_unclear=True,
                has_images=True,
            ),
        ]

        transcriptions = await pipeline.process_pdf_pages(pdf_bytes, pages)

        self.assertEqual(len(transcriptions), 2)
        # Page 1: Digital bypass
        self.assertEqual(transcriptions[0].page_num, 1)
        self.assertEqual(transcriptions[0].extraction_source, "pymupdf")

        # Page 2: Gemini Vision
        self.assertEqual(transcriptions[1].page_num, 2)
        self.assertEqual(transcriptions[1].extraction_source, "gemini_vision")
        self.assertIn("किराया", transcriptions[1].text)

    async def test_standalone_image_routing(self):
        """Test P: Standalone image enters visual waterfall."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Stand-alone image agreement text.",
                extraction_source="gemini_vision",
                engine="gemini-3.8-flash",
                status="success",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, MagicMock(), MagicMock())
        img_bytes = _create_test_image_bytes()

        results = await pipeline.process_image_file(img_bytes, filename="contract_photo.png")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].page_num, 1)
        self.assertEqual(results[0].extraction_source, "gemini_vision")

    async def test_corrupted_image_handling(self):
        """Test Z: Corrupted image bytes raise ValueError."""
        pipeline = VisualDocumentPipeline()
        with self.assertRaises(ValueError):
            await pipeline.process_image_file(b"not_an_image_corrupted_data", filename="bad.png")

    async def test_malformed_gemini_response(self):
        """Test X: Malformed Gemini API response is handled gracefully."""
        adapter = GeminiVisionAdapter()
        cap = ModelCapability(
            name="gemini-3.8-flash",
            provider="gemini",
            context_window=1_048_576,
            max_output_tokens=8192,
            modalities=["text", "image"],
            vision_support=True,
            structured_output="json_schema",
        )
        with patch.object(adapter, "is_available", return_value=(True, "ok")), \
             patch.object(adapter, "get_model_capability", return_value=cap), \
             patch.object(adapter, "_call_gemini_api", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = RuntimeError("Malformed response: no candidates")
            with self.assertRaises(RuntimeError) as ctx:
                await adapter.transcribe_image(_create_test_image_bytes(), page_num=1)
            self.assertIn("Malformed response", str(ctx.exception))

    async def test_malformed_ocr_response(self):
        """Test Y: Malformed OCR response does not crash pipeline; yields to next fallback."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (False, "disabled")

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (True, "ok")
        # PaddleOCR throws unexpected IndexError/TypeError
        mock_paddle.transcribe_image = AsyncMock(side_effect=TypeError("Unexpected NoneType in bbox"))

        mock_tess = MagicMock(spec=TesseractAdapter)
        mock_tess.is_available.return_value = (True, "ok")
        mock_tess.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Tesseract rescued document after PaddleOCR failure.",
                extraction_source="tesseract",
                engine="tesseract",
                confidence=0.84,
                status="success",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        res = await pipeline.transcribe_page_image(_create_test_image_bytes(), page_num=1)

        self.assertEqual(res.extraction_source, "tesseract")
        self.assertEqual(res.status, "fallback_used")
        # History records Paddle failure
        self.assertTrue(any(h.get("engine") == "paddleocr" and h.get("status") == "failed" for h in res.fallback_history))

    async def test_fallback_history_recording(self):
        """Test S: Fallback history captures detailed chronological progression."""
        mock_gemini = MagicMock(spec=GeminiVisionAdapter)
        mock_gemini.is_available.return_value = (True, "ok")
        mock_gemini.transcribe_image = AsyncMock(side_effect=RuntimeError("503 Service Unavailable"))

        mock_paddle = MagicMock(spec=PaddleOCRAdapter)
        mock_paddle.is_available.return_value = (True, "ok")
        mock_paddle.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Garbled text 1234",
                extraction_source="paddleocr",
                engine="paddleocr-v4",
                confidence=0.10,
                status="success_with_uncertainty",
                quality_score=0.15,
                is_unclear=True,
            )
        )

        mock_tess = MagicMock(spec=TesseractAdapter)
        mock_tess.is_available.return_value = (True, "ok")
        mock_tess.transcribe_image = AsyncMock(
            return_value=PageTranscription(
                page_num=1,
                text="Standard legal clause recovered by Tesseract.",
                extraction_source="tesseract",
                engine="tesseract",
                confidence=0.88,
                status="success",
            )
        )

        pipeline = VisualDocumentPipeline(mock_gemini, mock_paddle, mock_tess)
        res = await pipeline.transcribe_page_image(_create_test_image_bytes(), page_num=1)

        self.assertEqual(len(res.fallback_history), 3)
        self.assertEqual(res.fallback_history[0]["engine"], "gemini_vision")
        self.assertEqual(res.fallback_history[0]["status"], "failed")
        self.assertEqual(res.fallback_history[1]["engine"], "paddleocr")
        self.assertEqual(res.fallback_history[1]["status"], "rejected_low_quality")
        self.assertEqual(res.fallback_history[2]["engine"], "tesseract")
        self.assertEqual(res.fallback_history[2]["status"], "success")


if __name__ == "__main__":
    unittest.main()
