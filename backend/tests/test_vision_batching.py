"""Tests for batched Gemini Vision reading of scanned / handwritten pages (no network)."""

import unittest
from unittest.mock import AsyncMock, patch

import fitz

from services.page_content import PageContent
from services.page_transcription import PageTranscription
from services.vision_pipeline import GeminiVisionAdapter, VisualDocumentPipeline, split_batch_pages

GOOD_TEXT = "This is a handwritten rent receipt acknowledging payment of rupees five thousand for the month of June."


def _blank_pdf(n: int) -> bytes:
    doc = fitz.open()
    for _ in range(n):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def _scanned_pages(n: int):
    return [PageContent(page_num=i + 1, text="", extraction_source="pymupdf", script="Latin / English",
                        page_type="scanned", has_images=True, image_count=1, is_unclear=True) for i in range(n)]


def _trans(num: int, text: str = GOOD_TEXT) -> PageTranscription:
    return PageTranscription(page_num=num, text=text, extraction_source="gemini_vision", engine="gemini-2.5-flash")


class TestSplitBatchPages(unittest.TestCase):
    def test_splits_on_markers_and_ignores_preamble(self):
        raw = "preamble\n=== PAGE 3 ===\nfirst text\n=== PAGE 4 ===\nsecond text"
        self.assertEqual(split_batch_pages(raw, [3, 4]), {3: "first text", 4: "second text"})

    def test_ignores_unexpected_and_duplicate_pages(self):
        raw = "=== PAGE 1 ===\na\n=== PAGE 9 ===\nzzz\n=== PAGE 1 ===\nb"
        self.assertEqual(split_batch_pages(raw, [1, 2]), {1: "a"})

    def test_single_page_without_markers_is_accepted(self):
        self.assertEqual(split_batch_pages("just text", [5]), {5: "just text"})

    def test_multi_page_without_markers_is_rejected(self):
        self.assertEqual(split_batch_pages("just text", [1, 2]), {})


class TestBatchTranscription(unittest.IsolatedAsyncioTestCase):
    def _pipeline(self, batch_pages: int = 2):
        adapter = GeminiVisionAdapter()
        pipe = VisualDocumentPipeline(gemini_adapter=adapter)
        pipe.settings = type("S", (), {"vision_batch_pages": batch_pages})()
        return pipe, adapter

    async def test_pages_are_sent_in_batches_and_collected(self):
        pipe, adapter = self._pipeline(batch_pages=2)
        calls = []

        async def fake_batch(batch, mime_type="image/jpeg"):
            calls.append([p for p, _ in batch])
            return {p: _trans(p) for p, _ in batch}

        with patch.object(adapter, "is_available", return_value=(True, "ok")), \
             patch.object(adapter, "transcribe_images_batch", new=fake_batch):
            out = await pipe._batch_transcribe_scanned_pages(_blank_pdf(5), _scanned_pages(5))
        self.assertEqual(sorted(calls), [[1, 2], [3, 4], [5]])
        self.assertEqual(sorted(out), [1, 2, 3, 4, 5])
        self.assertEqual(out[1].fallback_history[0]["engine"], "gemini_vision_batch")

    async def test_low_quality_pages_are_left_for_the_fallback_chain(self):
        pipe, adapter = self._pipeline(batch_pages=4)

        async def fake_batch(batch, mime_type="image/jpeg"):
            return {1: _trans(1), 2: _trans(2, "xx")}   # page 2 unreadable

        with patch.object(adapter, "is_available", return_value=(True, "ok")), \
             patch.object(adapter, "transcribe_images_batch", new=fake_batch):
            out = await pipe._batch_transcribe_scanned_pages(_blank_pdf(2), _scanned_pages(2))
        self.assertEqual(sorted(out), [1])

    async def test_batch_failure_returns_empty_so_per_page_path_runs(self):
        pipe, adapter = self._pipeline()
        with patch.object(adapter, "is_available", return_value=(True, "ok")), \
             patch.object(adapter, "transcribe_images_batch", new=AsyncMock(side_effect=RuntimeError("HTTP 429"))):
            out = await pipe._batch_transcribe_scanned_pages(_blank_pdf(3), _scanned_pages(3))
        self.assertEqual(out, {})

    async def test_disabled_when_gemini_unavailable_or_batching_off(self):
        pipe, adapter = self._pipeline()
        with patch.object(adapter, "is_available", return_value=(False, "no key")):
            self.assertEqual(await pipe._batch_transcribe_scanned_pages(_blank_pdf(3), _scanned_pages(3)), {})
        pipe2, adapter2 = self._pipeline(batch_pages=1)
        with patch.object(adapter2, "is_available", return_value=(True, "ok")):
            self.assertEqual(await pipe2._batch_transcribe_scanned_pages(_blank_pdf(3), _scanned_pages(3)), {})


if __name__ == "__main__":
    unittest.main()
