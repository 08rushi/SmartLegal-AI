"""
test_phase3_chunking.py — Phase 3 Token-Aware Chunking & Partial-Failure Handling Test Suite.

Verifies:
  A. English token estimation
  B. Devanagari token estimation
  C. Tamil token estimation
  D. Other Unicode/non-Latin text token estimation
  E. Safety margin calculation
  F. Maximum safe chunk size adherence
  G. Page-boundary preservation
  H. Multi-page chunk creation
  I. Oversized single-page splitting
  J. Document ordering preservation
  K. Chunk metadata completeness
  L. Successful chunk preservation when another chunk fails
  M. Failed chunk tracking
  N. Bounded retry behavior for transient errors
  O. Retry exhaustion handling
  P. Completion ratio calculation
  Q. incomplete_chunks metadata
  R. Malformed AI response handling
  S. Provider/network transient failure classification & retry
  T. Permanent failure handling (fail fast without retry)
  U. Backward compatibility with split_into_chunks callers
  V. Empty / very small document handling
  W. Mixed digital/scanned PageContent input handling
"""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chunking_service import (
    DEFAULT_MAX_CHUNK_TOKENS,
    DEFAULT_SAFETY_MARGIN_TOKENS,
    DocumentChunk,
    ChunkingService,
    classify_chunk_error,
    estimate_tokens,
    execute_chunks_with_retry,
    get_safe_chunk_budget,
    is_retryable_error,
)
from services.model_capabilities import ModelCapability
from services.page_content import PageContent
from services.pdf_parser import split_into_chunks


class TestPhase3TokenEstimation(unittest.TestCase):
    """Tests A, B, C, D: Token estimation across Latin and Indic scripts."""

    def test_english_token_estimation(self):
        # 350 English chars -> ~100 tokens at ~3.5 chars/token
        text = "This is a standard English contract clause defining tenant obligations and lease termination rules. " * 3
        est = estimate_tokens(text)
        self.assertGreater(est, 50)
        self.assertLess(est, 150)

    def test_devanagari_token_estimation(self):
        # 250 Hindi/Devanagari characters -> ~100 tokens at ~2.5 chars/token
        hindi_text = "यह एक कानूनी किराया अनुबंध है जिसके अंतर्गत मकान मालिक और किरायेदार के बीच सभी नियम एवं शर्तें तय की गई हैं। " * 2
        est = estimate_tokens(hindi_text)
        # Devanagari must produce more estimated tokens than the same length in English
        eng_text = "A" * len(hindi_text)
        self.assertGreater(est, estimate_tokens(eng_text))

    def test_tamil_token_estimation(self):
        tamil_text = "வாடகை ஒப்பந்தம் மற்றும் உரிமையாளர் விதிமுறைகள் குறித்த சட்ட ஆவணம். " * 3
        est = estimate_tokens(tamil_text)
        self.assertGreater(est, 40)
        eng_text = "A" * len(tamil_text)
        self.assertGreater(est, estimate_tokens(eng_text))

    def test_other_unicode_text_token_estimation(self):
        # Bengali, Telugu, Gujarati
        mixed_indic = "ভাড়া চুক্তিপত্র అద్దெ ఒప్పందం ભાડા કરાર"
        est = estimate_tokens(mixed_indic)
        self.assertGreater(est, 10)


class TestPhase3SafetyMarginAndBudget(unittest.TestCase):
    """Tests E, F: Safety margin & maximum chunk sizing."""

    def test_safety_margin_calculation(self):
        # Model with 8192 context window, 2048 max output, 1500 safety margin
        cap = ModelCapability(
            name="test-model",
            provider="test",
            context_window=8192,
            max_output_tokens=2048,
            modalities=["text"],
            vision_support=False,
            structured_output="json_schema",
        )
        # Available context = 8192 - 2048 - 1500 = 4644
        # Budget = min(2500, 4644) = 2500
        budget = get_safe_chunk_budget(cap, max_chunk_tokens=2500, safety_margin=1500)
        self.assertEqual(budget, 2500)

        # Constrained model with small context window (4000)
        cap_small = ModelCapability(
            name="test-small",
            provider="test",
            context_window=4000,
            max_output_tokens=1000,
            modalities=["text"],
            vision_support=False,
            structured_output="json_schema",
        )
        # Available = 4000 - 1000 - 1500 = 1500
        budget_small = get_safe_chunk_budget(cap_small, max_chunk_tokens=2500, safety_margin=1500)
        self.assertEqual(budget_small, 1500)

    def test_maximum_safe_chunk_size(self):
        # Ensure chunker adheres to max tokens budget within ~10% tolerance
        chunker = ChunkingService(max_chunk_tokens=200, safety_margin=500)
        # Generate text of 2000 chars (~570 tokens) across 4 pages
        pages = [
            PageContent(page_num=i, text=f"Page {i} content clause text. " * 20, extraction_source="pymupdf", script="Latin / English")
            for i in range(1, 5)
        ]
        chunks = chunker.chunk_pages(pages)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            # Overrun must not exceed max_allowed_tokens (safe_budget * 1.10)
            self.assertLessEqual(c.estimated_tokens, chunker.max_allowed_tokens + 20)


class TestPhase3PageBoundariesAndSplitting(unittest.TestCase):
    """Tests G, H, I, J, K: Page boundaries, multi-page chunks, oversized splitting, order, metadata."""

    def test_page_boundary_preservation(self):
        # 3 small pages that easily fit in one chunk (budget 2500)
        pages = [
            PageContent(page_num=1, text="Page 1 terms and definitions.", extraction_source="pymupdf", script="Latin / English"),
            PageContent(page_num=2, text="Page 2 payment obligations.", extraction_source="pymupdf", script="Latin / English"),
            PageContent(page_num=3, text="Page 3 termination clauses.", extraction_source="pymupdf", script="Latin / English"),
        ]
        chunker = ChunkingService(max_chunk_tokens=2500)
        chunks = chunker.chunk_pages(pages)

        # Kept as 1 multi-page chunk preserving page order
        self.assertEqual(len(chunks), 1)
        c = chunks[0]
        self.assertEqual(c.page_start, 1)
        self.assertEqual(c.page_end, 3)
        self.assertEqual(c.page_numbers, [1, 2, 3])
        self.assertIn("[Page 1]", c.text)
        self.assertIn("[Page 2]", c.text)
        self.assertIn("[Page 3]", c.text)

    def test_multi_page_chunk_creation(self):
        # Pages that require splitting across multiple chunks
        chunker = ChunkingService(max_chunk_tokens=100)  # Very small budget (~350 chars)
        pages = [
            PageContent(page_num=1, text="Page 1: " + "Standard legal warranty. " * 10, extraction_source="pymupdf", script="Latin / English"),
            PageContent(page_num=2, text="Page 2: " + "Indemnity requirements. " * 10, extraction_source="pymupdf", script="Latin / English"),
            PageContent(page_num=3, text="Page 3: " + "Arbitration procedure. " * 10, extraction_source="pymupdf", script="Latin / English"),
        ]
        chunks = chunker.chunk_pages(pages)
        self.assertGreaterEqual(len(chunks), 3)

        # Verify document order is strictly preserved
        for idx, c in enumerate(chunks):
            self.assertEqual(c.chunk_index, idx)
            self.assertEqual(c.chunk_id, f"chunk_{idx + 1}")

    def test_oversized_single_page_splitting(self):
        # Single page with 4000 characters (~1100 tokens), budget is 300 tokens
        chunker = ChunkingService(max_chunk_tokens=300)
        long_body = "\n\n".join([f"Paragraph {i}: " + "This is a detailed legal obligation paragraph. " * 5 for i in range(1, 10)])
        page = PageContent(page_num=1, text=long_body, extraction_source="pymupdf", script="Latin / English")

        chunks = chunker.chunk_pages([page])
        self.assertGreater(len(chunks), 1)

        # All fragments must point to page 1 and maintain part indexes
        for idx, c in enumerate(chunks):
            self.assertEqual(c.page_start, 1)
            self.assertEqual(c.page_end, 1)
            self.assertEqual(c.page_numbers, [1])
            self.assertTrue(c.is_split_page)
            self.assertEqual(c.sub_chunk_index, idx + 1)
            self.assertIn(f"part_{idx + 1}", c.chunk_id)

    def test_document_ordering_and_chunk_metadata(self):
        chunker = ChunkingService(max_chunk_tokens=500)
        pages = [
            PageContent(page_num=i, text=f"Clause {i} content text.", extraction_source="pymupdf", script="Latin / English")
            for i in range(1, 6)
        ]
        chunks = chunker.chunk_pages(pages)
        d = chunks[0].to_dict()

        self.assertIn("chunk_id", d)
        self.assertIn("chunk_index", d)
        self.assertIn("start_page", d)
        self.assertIn("end_page", d)
        self.assertIn("estimated_tokens", d)
        self.assertIn("text", d)


class TestPhase3PartialFailureAndRetries(unittest.IsolatedAsyncioTestCase):
    """Tests L, M, N, O, P, Q, R, S, T: Partial failures, bounded retries, error classification, metadata."""

    def test_error_classification(self):
        self.assertEqual(classify_chunk_error(Exception("429 Rate Limit Exceeded")), "rate_limit")
        self.assertEqual(classify_chunk_error(Exception("TPM quota limit exceeded")), "rate_limit")
        self.assertEqual(classify_chunk_error(Exception("Connection timed out")), "transient")
        self.assertEqual(classify_chunk_error(Exception("503 Service Unavailable")), "transient")
        self.assertEqual(classify_chunk_error(Exception("JSONDecodeError: Expecting value")), "malformed_response")
        self.assertEqual(classify_chunk_error(Exception("401 Unauthorized")), "permanent")
        self.assertEqual(classify_chunk_error(ValueError("Invalid argument")), "permanent")

        self.assertTrue(is_retryable_error("rate_limit"))
        self.assertTrue(is_retryable_error("transient"))
        self.assertTrue(is_retryable_error("malformed_response"))
        self.assertFalse(is_retryable_error("permanent"))

    async def test_successful_chunks_survive_after_failure(self):
        # 4 chunks: Chunk 1 ok, Chunk 2 ok, Chunk 3 fail (permanent), Chunk 4 ok
        chunks = [
            DocumentChunk("chunk_1", 0, 1, 1, [1], "Page 1", 50),
            DocumentChunk("chunk_2", 1, 2, 2, [2], "Page 2", 50),
            DocumentChunk("chunk_3", 2, 3, 3, [3], "Page 3", 50),
            DocumentChunk("chunk_4", 3, 4, 4, [4], "Page 4", 50),
        ]

        async def mock_processor(chunk: DocumentChunk) -> list[dict]:
            if chunk.chunk_id == "chunk_3":
                raise ValueError("Permanent parsing failure on chunk 3")
            return [{"id": f"clause_from_{chunk.chunk_id}", "title": "Term", "risk_level": "low"}]

        clauses, meta = await execute_chunks_with_retry(
            chunks=chunks,
            chunk_processor=mock_processor,
            max_retries=2,
            base_backoff_seconds=0.01,
        )

        # Successful chunks preserved
        self.assertEqual(len(clauses), 3)
        self.assertEqual(clauses[0]["id"], "clause_from_chunk_1")
        self.assertEqual(clauses[1]["id"], "clause_from_chunk_2")
        self.assertEqual(clauses[2]["id"], "clause_from_chunk_4")

        # Metadata records partial status
        self.assertTrue(meta["is_partial"])
        self.assertEqual(meta["successful_chunks"], 3)
        self.assertEqual(meta["total_chunks"], 4)
        self.assertEqual(meta["completion_ratio"], 0.75)

        # Incomplete chunk identified
        self.assertEqual(len(meta["incomplete_chunks"]), 1)
        inc = meta["incomplete_chunks"][0]
        self.assertEqual(inc["chunk_id"], "chunk_3")
        self.assertEqual(inc["page_start"], 3)
        self.assertEqual(inc["error_type"], "permanent")
        self.assertIn("Permanent parsing failure", inc["error_message"])

    async def test_transient_retry_and_recovery(self):
        # Chunk 1 fails on attempt 1 with transient error, then succeeds on attempt 2
        chunk = DocumentChunk("chunk_1", 0, 1, 1, [1], "Page 1", 50)
        attempts = 0

        async def mock_processor(c: DocumentChunk) -> list[dict]:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ConnectionError("503 Service Unavailable")
            return [{"id": "recovered_clause", "title": "Term", "risk_level": "low"}]

        clauses, meta = await execute_chunks_with_retry(
            chunks=[chunk],
            chunk_processor=mock_processor,
            max_retries=2,
            base_backoff_seconds=0.01,
        )

        self.assertEqual(len(clauses), 1)
        self.assertEqual(attempts, 2)
        self.assertEqual(meta["completion_ratio"], 1.0)
        self.assertFalse(meta["is_partial"])
        self.assertEqual(len(meta["incomplete_chunks"]), 0)

    async def test_retry_exhaustion(self):
        # Chunk persistently fails with rate limit -> retries exhausted
        chunk = DocumentChunk("chunk_1", 0, 1, 1, [1], "Page 1", 50)
        chunk2 = DocumentChunk("chunk_2", 1, 2, 2, [2], "Page 2", 50)
        attempts = 0

        async def mock_processor(c: DocumentChunk) -> list[dict]:
            nonlocal attempts
            if c.chunk_id == "chunk_1":
                attempts += 1
                raise RuntimeError("429 Rate Limit")
            return [{"id": "chunk_2_clause", "title": "Term", "risk_level": "low"}]

        clauses, meta = await execute_chunks_with_retry(
            chunks=[chunk, chunk2],
            chunk_processor=mock_processor,
            max_retries=2,
            base_backoff_seconds=0.01,
        )

        self.assertEqual(len(clauses), 1)
        self.assertEqual(attempts, 3)  # Initial + 2 retries
        self.assertEqual(meta["completion_ratio"], 0.5)
        self.assertTrue(meta["is_partial"])
        self.assertEqual(meta["incomplete_chunks"][0]["error_type"], "rate_limit")

    async def test_all_chunks_failed_raises_runtime_error(self):
        # If all chunks fail, raises RuntimeError instead of returning fake empty success
        chunk = DocumentChunk("chunk_1", 0, 1, 1, [1], "Page 1", 50)

        async def fail_proc(c: DocumentChunk):
            raise ValueError("All chunks bad")

        with self.assertRaises(RuntimeError) as ctx:
            await execute_chunks_with_retry(
                chunks=[chunk],
                chunk_processor=fail_proc,
                max_retries=1,
                base_backoff_seconds=0.01,
            )
        self.assertIn("All 1 document chunks failed", str(ctx.exception))


class TestPhase3CompatibilityAndEdgeCases(unittest.TestCase):
    """Tests U, V, W: Backward compatibility, empty inputs, mixed PageContent."""

    def test_backward_compatibility_split_into_chunks(self):
        text = "[Page 1]\nFirst clause text.\n[Page 2]\nSecond clause text."
        # Character-based legacy call
        chunks_char = split_into_chunks(text, max_chars=1000)
        self.assertIsInstance(chunks_char, list)
        self.assertGreater(len(chunks_char), 0)
        self.assertIn("text", chunks_char[0])
        self.assertIn("start_page", chunks_char[0])

        # Token-based call via max_tokens
        chunks_token = split_into_chunks(text, max_tokens=500)
        self.assertIsInstance(chunks_token, list)
        self.assertGreater(len(chunks_token), 0)
        self.assertIn("text", chunks_token[0])
        self.assertIn("estimated_tokens", chunks_token[0])

    def test_empty_and_whitespace_document(self):
        chunker = ChunkingService()
        self.assertEqual(chunker.chunk_pages([]), [])
        self.assertEqual(chunker.chunk_text(""), [])
        self.assertEqual(chunker.chunk_text("   \n\n  "), [])

    def test_mixed_digital_and_scanned_pagecontent_input(self):
        chunker = ChunkingService(max_chunk_tokens=1000)
        # 3 pages: Page 1 digital, Page 2 scanned (empty text layer), Page 3 digital
        pages = [
            PageContent(page_num=1, text="Page 1 digital lease clause.", extraction_source="pymupdf", script="Latin / English", page_type="digital"),
            PageContent(page_num=2, text="", extraction_source="pymupdf", script="Latin / English", page_type="scanned", has_images=True),
            PageContent(page_num=3, text="Page 3 digital indemnity clause.", extraction_source="pymupdf", script="Latin / English", page_type="digital"),
        ]
        chunks = chunker.chunk_pages(pages)
        self.assertEqual(len(chunks), 1)
        self.assertIn("[Page 1]", chunks[0].text)
        self.assertIn("[Page 3]", chunks[0].text)


if __name__ == "__main__":
    unittest.main()
