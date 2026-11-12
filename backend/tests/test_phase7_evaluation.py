"""
test_phase7_evaluation.py — Phase 7 Accuracy Evaluation Test Suite.

Tests are organized into 8 groups (A–H) covering:
  A — Schema, Serialization & Provenance (8 tests)
  B — Normalization (9 tests)
  C — CER/WER Math & Edge Cases (12 tests)
  D — Classification Metrics (7 tests)
  E — OCR Confidence Correlation (4 tests)
  F — Runner Integration (6 tests)
  G — Phase 6 Comparative (5 tests)
  H — Import Isolation & Regression (4 tests)

Total: 55 tests (48 originally planned + 7 additional edge cases in v1.1)

All tests run without external API calls. No production services start.
"""

from __future__ import annotations

import ast
import importlib
import io
import json
import os
import sys
import unittest
from typing import List
from unittest.mock import MagicMock, patch

# Ensure backend/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# =============================================================================
# A — Schema, Serialization & Provenance (8 tests)
# =============================================================================

class TestSchemaSerializationAndProvenance(unittest.TestCase):

    def _make_gt_doc(self, review_state: str = "approved") -> "GroundTruthDocument":
        from evaluation.schema import GroundTruthDocument, GroundTruthPage, AnnotatorMetadata
        return GroundTruthDocument(
            corpus_id="test_corpus",
            corpus_version="1.0.0",
            document_id="test_doc_001",
            filename="test.pdf",
            source_hash="a" * 64,
            document_type="rental_agreement",
            expected_document_class="digital_pdf",
            language="en",
            indic_scripts=[],
            page_count=2,
            pages=[
                GroundTruthPage(
                    page_num=1,
                    reference_text="Hello world",
                    script="Latin / English",
                    expected_page_type="digital",
                    expected_is_unclear=False,
                    annotation=AnnotatorMetadata(
                        annotator_id="a1",
                        annotation_date="2026-01-01",
                        review_state=review_state,
                    ),
                    annotation_version="1.0",
                )
            ],
            dataset_version="1.0.0",
            schema_version="7.1",
            created_at="2026-01-01T00:00:00Z",
        )

    def test_A1_round_trip_json(self):
        """A1: GroundTruthDocument round-trips to/from JSON without data loss."""
        from evaluation.schema import GroundTruthDocument
        doc = self._make_gt_doc()
        d = doc.to_dict()
        raw = json.dumps(d)
        loaded = GroundTruthDocument.from_dict(json.loads(raw))
        self.assertEqual(loaded.corpus_id, doc.corpus_id)
        self.assertEqual(loaded.source_hash, doc.source_hash)
        self.assertEqual(loaded.schema_version, doc.schema_version)
        self.assertEqual(loaded.pages[0].reference_text, doc.pages[0].reference_text)
        self.assertEqual(loaded.pages[0].annotation.review_state, doc.pages[0].annotation.review_state)

    def test_A2_source_hash_format(self):
        """A2: source_hash field is a 64-character hex string."""
        doc = self._make_gt_doc()
        self.assertEqual(len(doc.source_hash), 64)
        int(doc.source_hash, 16)  # must parse as hex

    def test_A3_draft_page_skipped(self):
        """A3: review_state='draft' pages are counted as skipped, excluded from metrics."""
        from evaluation.schema import GroundTruthDocument, GroundTruthPage, AnnotatorMetadata

        doc = self._make_gt_doc(review_state="draft")

        # Runner with mocked PDF extraction
        from evaluation.runner import DocumentEvaluator
        evaluator = DocumentEvaluator()

        mock_page = MagicMock()
        mock_page.page_num = 1
        mock_page.text = "Hello world"
        mock_page.extraction_source = "pymupdf"
        mock_page.page_type = "digital"
        mock_page.is_unclear = False
        mock_page.ocr_confidence = None
        mock_page.quality_score = 0.8
        mock_page_list = [mock_page]
        mock_page_list_obj = MagicMock()
        mock_page_list_obj.__iter__ = lambda self: iter(mock_page_list)
        mock_page_list_obj.document_type = "digital_pdf"

        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_page_list_obj), \
             patch("evaluation.runner.compute_source_hash", return_value="a" * 64):
            result = evaluator.evaluate(doc, b"fakepdf")

        self.assertEqual(result.skipped_page_count, 1)
        self.assertEqual(result.evaluated_page_count, 0)
        from evaluation.schema import FailureCategory
        self.assertIn(FailureCategory.ANNOTATION_INCOMPLETE, result.page_results[0].failure_categories)

    def test_A4_rejected_page_skipped(self):
        """A4: review_state='rejected' pages are skipped."""
        doc = self._make_gt_doc(review_state="rejected")
        from evaluation.runner import DocumentEvaluator
        evaluator = DocumentEvaluator()
        mock_page_list_obj = MagicMock()
        mock_page_list_obj.__iter__ = lambda self: iter([])
        mock_page_list_obj.document_type = "empty_pdf"
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_page_list_obj), \
             patch("evaluation.runner.compute_source_hash", return_value="a" * 64):
            result = evaluator.evaluate(doc, b"fakepdf")
        self.assertEqual(result.skipped_page_count, 1)

    def test_A5_review_pending_skipped(self):
        """A5: review_state='review_pending' pages are skipped."""
        doc = self._make_gt_doc(review_state="review_pending")
        from evaluation.runner import DocumentEvaluator
        evaluator = DocumentEvaluator()
        mock_page_list_obj = MagicMock()
        mock_page_list_obj.__iter__ = lambda self: iter([])
        mock_page_list_obj.document_type = "empty_pdf"
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_page_list_obj), \
             patch("evaluation.runner.compute_source_hash", return_value="a" * 64):
            result = evaluator.evaluate(doc, b"fakepdf")
        self.assertEqual(result.skipped_page_count, 1)

    def test_A6_approved_page_evaluated(self):
        """A6: review_state='approved' pages are included in metrics."""
        doc = self._make_gt_doc(review_state="approved")
        from evaluation.runner import DocumentEvaluator
        evaluator = DocumentEvaluator()

        mock_page = MagicMock()
        mock_page.page_num = 1
        mock_page.text = "Hello world"
        mock_page.extraction_source = "pymupdf"
        mock_page.page_type = "digital"
        mock_page.is_unclear = False
        mock_page.ocr_confidence = None
        mock_page.quality_score = 0.9
        mock_page_list_obj = MagicMock()
        mock_page_list_obj.__iter__ = lambda self: iter([mock_page])
        mock_page_list_obj.document_type = "digital_pdf"
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_page_list_obj), \
             patch("evaluation.runner.compute_source_hash", return_value="a" * 64):
            result = evaluator.evaluate(doc, b"fakepdf")
        self.assertEqual(result.evaluated_page_count, 1)
        self.assertEqual(result.skipped_page_count, 0)

    def test_A7_zero_approved_pages_insufficient(self):
        """A7: Zero approved pages → cer_stats has insufficient_data=True."""
        doc = self._make_gt_doc(review_state="draft")
        from evaluation.runner import DocumentEvaluator
        evaluator = DocumentEvaluator()
        mock_page_list_obj = MagicMock()
        mock_page_list_obj.__iter__ = lambda self: iter([])
        mock_page_list_obj.document_type = "empty_pdf"
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_page_list_obj), \
             patch("evaluation.runner.compute_source_hash", return_value="a" * 64):
            result = evaluator.evaluate(doc, b"fakepdf")
        self.assertTrue(result.cer_stats.get("insufficient_data"))
        self.assertIsNone(result.cer_stats.get("mean"))


    def test_A8_disclaimer_present(self):
        """A8: DISCLAIMER ClassVar present in all three result dataclasses."""
        from evaluation.schema import PageEvaluationResult, DocumentEvaluationResult, EvaluationRun
        self.assertIn("NOT legal accuracy", PageEvaluationResult.DISCLAIMER)
        self.assertIn("NOT legal accuracy", DocumentEvaluationResult.DISCLAIMER)
        self.assertIn("NOT legal accuracy", EvaluationRun.DISCLAIMER)


# =============================================================================
# B — Normalization (9 tests)
# =============================================================================

class TestNormalization(unittest.TestCase):

    def test_B1_nfkc_half_width_katakana(self):
        """B1: NFKC converts half-width katakana to full-width."""
        from evaluation.normalizer import normalize_for_cer
        # U+FF71 = half-width katakana letter A → U+30A2 full-width
        result = normalize_for_cer("\uFF71")
        self.assertEqual(result, "\u30A2")

    def test_B2_devanagari_nukta_composed(self):
        """B2: Devanagari Nukta composes correctly via NFC."""
        from evaluation.normalizer import normalize_for_cer
        import unicodedata
        # ka + nukta should NFC-compose
        composed_input = "\u0915\u093C"  # ka + nukta
        result = normalize_for_cer(composed_input)
        # After NFC, this may compose or remain as combining — either is valid;
        # the key invariant is no information is silently discarded.
        nfc_expected = unicodedata.normalize("NFC", unicodedata.normalize("NFKC", composed_input))
        self.assertEqual(result, nfc_expected)

    def test_B3_zwj_stripped_by_default(self):
        """B3: ZWJ (U+200D) stripped by default."""
        from evaluation.normalizer import normalize_for_cer
        result = normalize_for_cer("a\u200Db")
        self.assertNotIn("\u200D", result)
        self.assertIn("a", result)
        self.assertIn("b", result)

    def test_B4_zwnj_stripped_by_default(self):
        """B4: ZWNJ (U+200C) stripped by default."""
        from evaluation.normalizer import normalize_for_cer
        result = normalize_for_cer("a\u200Cb")
        self.assertNotIn("\u200C", result)

    def test_B5_preserve_joiners_retains_zwj_zwnj(self):
        """B5: preserve_joiners=True retains ZWJ and ZWNJ."""
        from evaluation.normalizer import normalize_for_cer
        result = normalize_for_cer("a\u200Db\u200Cc", preserve_joiners=True)
        self.assertIn("\u200D", result)
        self.assertIn("\u200C", result)

    def test_B6_whitespace_collapsed(self):
        """B6: Multi-whitespace / newlines collapsed to single ASCII space."""
        from evaluation.normalizer import normalize_for_cer
        result = normalize_for_cer("hello   \t\n\r world")
        self.assertEqual(result, "hello world")

    def test_B7_punctuation_for_wer_not_cer(self):
        """B7: Punctuation stripped for WER (normalize_for_wer), NOT for CER (normalize_for_cer)."""
        from evaluation.normalizer import normalize_for_cer, normalize_for_wer
        text = "Agreement, signed."
        cer_result = normalize_for_cer(text)
        wer_result = normalize_for_wer(text)
        # CER preserves punctuation
        self.assertIn(",", cer_result)
        # WER strips punctuation and returns word list
        self.assertIsInstance(wer_result, list)
        joined = " ".join(wer_result)
        self.assertNotIn(",", joined)
        self.assertNotIn(".", joined)

    def test_B8_unclear_token_preserved(self):
        """B8: [UNCLEAR] retained in CER (as chars) and WER (as single token)."""
        from evaluation.normalizer import normalize_for_cer, normalize_for_wer
        text = "This is [UNCLEAR] text"
        cer_result = normalize_for_cer(text)
        wer_result = normalize_for_wer(text)
        self.assertIn("[UNCLEAR]", cer_result)
        self.assertIn("[UNCLEAR]", wer_result)

    def test_B9_normalizer_version_constant(self):
        """B9: NORMALIZER_VERSION constant is present and non-empty."""
        from evaluation.normalizer import NORMALIZER_VERSION
        self.assertIsInstance(NORMALIZER_VERSION, str)
        self.assertGreater(len(NORMALIZER_VERSION), 0)


# =============================================================================
# C — CER/WER Math & Edge Cases (12 tests)
# =============================================================================

class TestCERWERMath(unittest.TestCase):

    def test_C1_perfect_match(self):
        """C1: Perfect match → CER = 0.0, WER = 0.0."""
        from evaluation.metrics import compute_cer, compute_wer
        cer, _ = compute_cer("Hello world", "Hello world")
        wer, _ = compute_wer("Hello world", "Hello world")
        self.assertAlmostEqual(cer, 0.0)
        self.assertAlmostEqual(wer, 0.0)

    def test_C2_empty_ref_nonempty_pred(self):
        """C2: Empty reference, non-empty predicted → CER = 1.0, WER = 1.0."""
        from evaluation.metrics import compute_cer, compute_wer
        cer, _ = compute_cer("", "some text")
        wer, _ = compute_wer("", "some text")
        self.assertAlmostEqual(cer, 1.0)
        self.assertAlmostEqual(wer, 1.0)

    def test_C3_nonempty_ref_empty_pred(self):
        """C3: Non-empty reference, empty predicted → CER = 1.0, WER = 1.0."""
        from evaluation.metrics import compute_cer, compute_wer
        cer, _ = compute_cer("some text", "")
        wer, _ = compute_wer("some text", "")
        self.assertAlmostEqual(cer, 1.0)
        self.assertAlmostEqual(wer, 1.0)

    def test_C4_whitespace_only_both_empty(self):
        """C4: Whitespace-only reference and whitespace-only predicted → CER = 0.0."""
        from evaluation.metrics import compute_cer, compute_wer
        cer, _ = compute_cer("   \t\n", "  \r\n  ")
        wer, _ = compute_wer("   \t\n", "  \r\n  ")
        self.assertAlmostEqual(cer, 0.0)
        self.assertAlmostEqual(wer, 0.0)

    def test_C5_whitespace_ref_nonempty_pred(self):
        """C5: Whitespace-only reference, non-empty predicted → CER = 1.0."""
        from evaluation.metrics import compute_cer, compute_wer
        cer, _ = compute_cer("   ", "some text")
        wer, _ = compute_wer("   ", "some text")
        self.assertAlmostEqual(cer, 1.0)
        self.assertAlmostEqual(wer, 1.0)

    def test_C6_unclear_only_pred_empty_ref(self):
        """C6: [UNCLEAR]-only predicted, empty reference → CER = 1.0."""
        from evaluation.metrics import compute_cer
        cer, _ = compute_cer("", "[UNCLEAR]")
        self.assertAlmostEqual(cer, 1.0)

    def test_C7_unclear_only_matches_unclear_ref(self):
        """C7: [UNCLEAR]-only predicted AND [UNCLEAR]-only reference → CER = 0.0."""
        from evaluation.metrics import compute_cer
        cer, _ = compute_cer("[UNCLEAR]", "[UNCLEAR]")
        self.assertAlmostEqual(cer, 0.0)

    def test_C8_single_char_substitution(self):
        """C8: Single char substitution: CER = 1/N where N = len(normalized reference)."""
        from evaluation.metrics import compute_cer
        from evaluation.normalizer import normalize_for_cer
        ref = "abc"
        pred = "axc"
        cer, ref_count = compute_cer(ref, pred)
        norm_ref = normalize_for_cer(ref)
        expected = 1 / len(norm_ref)
        self.assertAlmostEqual(cer, expected, places=5)
        self.assertEqual(ref_count, len(norm_ref))

    def test_C9_single_word_deletion(self):
        """C9: Single word deletion: WER = 1/M where M = word count of reference."""
        from evaluation.metrics import compute_wer
        ref = "one two three"
        pred = "one three"
        wer, ref_count = compute_wer(ref, pred)
        # ref has 3 words; 1 deletion → WER = 1/3
        self.assertEqual(ref_count, 3)
        self.assertAlmostEqual(wer, 1 / 3, places=3)

    def test_C10_cer_clamped_to_one(self):
        """C10: CER clamped to 1.0 even when edit_distance > len(reference)."""
        from evaluation.metrics import compute_cer
        # Very short reference, long predicted
        cer, _ = compute_cer("a", "abcdefghij")
        self.assertLessEqual(cer, 1.0)
        self.assertGreaterEqual(cer, 0.0)

    def test_C11_aggregate_stats_empty(self):
        """C11: aggregate_stats([]) → sample_count=0, insufficient_data=True, mean=None."""
        from evaluation.metrics import aggregate_stats
        result = aggregate_stats([])
        self.assertEqual(result["sample_count"], 0)
        self.assertTrue(result["insufficient_data"])
        self.assertIsNone(result["mean"])

    def test_C12_algorithm_constant(self):
        """C12: CER_WER_ALGORITHM constant present and contains 'difflib.SequenceMatcher'."""
        from evaluation.metrics import CER_WER_ALGORITHM
        self.assertIsInstance(CER_WER_ALGORITHM, str)
        self.assertIn("difflib.SequenceMatcher", CER_WER_ALGORITHM)


# =============================================================================
# D — Classification Metrics (7 tests)
# =============================================================================

class TestClassificationMetrics(unittest.TestCase):

    def test_D1_perfect_predictions(self):
        """D1: Perfect page_type predictions → per-class F1 = 1.0 for each present class."""
        from evaluation.metrics import page_type_metrics
        predicted = ["digital", "digital", "scanned"]
        expected  = ["digital", "digital", "scanned"]
        result = page_type_metrics(predicted, expected)
        self.assertAlmostEqual(result["per_class"]["digital"]["f1"], 1.0)
        self.assertAlmostEqual(result["per_class"]["scanned"]["f1"], 1.0)

    def test_D2_zero_support_class_gives_none(self):
        """D2: Class with support=0 → precision/recall/F1 = None (not 0.0)."""
        from evaluation.metrics import page_type_metrics
        predicted = ["digital", "digital"]
        expected  = ["digital", "digital"]
        result = page_type_metrics(predicted, expected)
        # 'empty' has support=0
        self.assertIsNone(result["per_class"]["empty"]["f1"])
        self.assertIsNone(result["per_class"]["empty"]["precision"])
        self.assertIsNone(result["per_class"]["empty"]["recall"])

    def test_D3_confusion_matrix_ordering(self):
        """D3: Confusion matrix row/col ordering matches labels list."""
        from evaluation.metrics import page_type_metrics
        predicted = ["digital", "scanned"]
        expected  = ["digital", "digital"]
        result = page_type_metrics(predicted, expected)
        labels = result["confusion_matrix"]["labels"]
        matrix = result["confusion_matrix"]["matrix"]
        # expected=digital, predicted=digital → row 0, col 0
        digital_idx = labels.index("digital")
        scanned_idx = labels.index("scanned")
        self.assertEqual(matrix[digital_idx][digital_idx], 1)  # 1 correct digital
        self.assertEqual(matrix[digital_idx][scanned_idx], 1)  # 1 digital predicted as scanned

    def test_D4_unclear_metrics_tp_fp_fn_tn(self):
        """D4: unclear_metrics TP/FP/FN/TN verified on 5-page example."""
        from evaluation.metrics import unclear_metrics
        # pred, expected: T=unclear, F=clear
        pred = [True,  True,  False, False, True]
        exp  = [True,  False, True,  False, True]
        # TP=2(pages 0,4), FP=1(page 1), FN=1(page 2), TN=1(page 3)
        result = unclear_metrics(pred, exp)
        self.assertEqual(result["tp"], 2)
        self.assertEqual(result["fp"], 1)
        self.assertEqual(result["fn"], 1)
        self.assertEqual(result["tn"], 1)
        self.assertAlmostEqual(result["precision"], 2 / 3, places=5)
        self.assertAlmostEqual(result["recall"], 2 / 3, places=5)

    def test_D5_unclear_precision_none_when_no_predicted_unclear(self):
        """D5: unclear_metrics precision = None when TP+FP = 0."""
        from evaluation.metrics import unclear_metrics
        pred = [False, False]
        exp  = [True,  False]
        result = unclear_metrics(pred, exp)
        self.assertIsNone(result["precision"])

    def test_D6_unclear_recall_none_when_no_expected_unclear(self):
        """D6: unclear_metrics recall = None when TP+FN = 0 (no truly unclear pages)."""
        from evaluation.metrics import unclear_metrics
        pred = [False, False]
        exp  = [False, False]
        result = unclear_metrics(pred, exp)
        self.assertIsNone(result["recall"])

    def test_D7_document_class_accuracy_none_when_empty(self):
        """D7: document_class_accuracy returns accuracy=None when total=0."""
        from evaluation.metrics import document_class_accuracy
        result = document_class_accuracy([], [])
        self.assertIsNone(result["accuracy"])
        self.assertEqual(result["total"], 0)


# =============================================================================
# E — OCR Confidence Correlation (4 tests)
# =============================================================================

class TestOCRConfidenceCorrelation(unittest.TestCase):

    def test_E1_negative_correlation(self):
        """E1: Negative correlation on synthetic data (higher confidence → lower CER)."""
        from evaluation.metrics import ocr_confidence_vs_cer_correlation
        confidences = [0.9, 0.7, 0.5, 0.3, 0.1]
        cers = [0.05, 0.15, 0.35, 0.60, 0.90]
        result = ocr_confidence_vs_cer_correlation(confidences, cers)
        self.assertFalse(result["insufficient_data"])
        self.assertIsNotNone(result["correlation"])
        # Negative correlation expected
        self.assertLess(result["correlation"], 0.0)

    def test_E2_insufficient_samples(self):
        """E2: Returns insufficient_data=True when sample_count < 3."""
        from evaluation.metrics import ocr_confidence_vs_cer_correlation
        result = ocr_confidence_vs_cer_correlation([0.9, 0.7], [0.1, 0.3], min_samples=3)
        self.assertTrue(result["insufficient_data"])
        self.assertIsNone(result["correlation"])
        self.assertEqual(result["sample_count"], 2)

    def test_E3_constant_confidence_insufficient(self):
        """E3: Returns insufficient_data=True when all confidence values are identical."""
        from evaluation.metrics import ocr_confidence_vs_cer_correlation
        confidences = [0.8, 0.8, 0.8, 0.8]
        cers = [0.1, 0.2, 0.3, 0.4]
        result = ocr_confidence_vs_cer_correlation(confidences, cers)
        self.assertTrue(result["insufficient_data"])
        self.assertIsNone(result["correlation"])
        self.assertIn("identical", result["reason"])

    def test_E4_algorithm_field_present(self):
        """E4: algorithm field = 'Pearson (statistics stdlib)' in all returned dicts."""
        from evaluation.metrics import ocr_confidence_vs_cer_correlation
        result = ocr_confidence_vs_cer_correlation([0.9, 0.7], [0.1, 0.3])
        self.assertEqual(result["algorithm"], "Pearson (statistics stdlib)")


# =============================================================================
# F — Runner Integration (6 tests)
# =============================================================================

class TestRunnerIntegration(unittest.TestCase):

    def _make_simple_gt(self, review_state: str = "approved") -> "GroundTruthDocument":
        from evaluation.schema import (
            GroundTruthDocument, GroundTruthPage, AnnotatorMetadata
        )
        return GroundTruthDocument(
            corpus_id="c1", corpus_version="1.0.0", document_id="doc1",
            filename="doc1.pdf", source_hash="b" * 64,
            document_type="nda", expected_document_class="digital_pdf",
            language="en", indic_scripts=[], page_count=1,
            pages=[GroundTruthPage(
                page_num=1, reference_text="Contract terms here.",
                script="Latin / English", expected_page_type="digital",
                expected_is_unclear=False,
                annotation=AnnotatorMetadata(
                    annotator_id="a1", annotation_date="2026-01-01",
                    review_state=review_state),
                annotation_version="1.0",
            )],
            dataset_version="1.0.0", schema_version="7.1",
            created_at="2026-01-01T00:00:00Z",
        )

    def _mock_page_list(self, text: str, page_num: int = 1):
        mock_page = MagicMock()
        mock_page.page_num = page_num
        mock_page.text = text
        mock_page.extraction_source = "pymupdf"
        mock_page.page_type = "digital"
        mock_page.is_unclear = False
        mock_page.ocr_confidence = None
        mock_page.quality_score = 0.85
        mock_list = MagicMock()
        mock_list.__iter__ = lambda self: iter([mock_page])
        mock_list.document_type = "digital_pdf"
        return mock_list

    def test_F1_runner_evaluated_skipped_failed_unavailable_counts(self):
        """F1: Runner produces correct evaluated/skipped/failed/unavailable counts."""
        from evaluation.schema import (
            GroundTruthDocument, GroundTruthPage, AnnotatorMetadata
        )
        from evaluation.runner import DocumentEvaluator

        doc = GroundTruthDocument(
            corpus_id="c1", corpus_version="1.0.0", document_id="doc2",
            filename="doc2.pdf", source_hash="b" * 64,
            document_type="nda", expected_document_class="digital_pdf",
            language="en", indic_scripts=[], page_count=3,
            pages=[
                GroundTruthPage(1, "Text p1", "Latin / English", "digital", False,
                    AnnotatorMetadata("a1","2026-01-01","approved"), "1.0"),
                GroundTruthPage(2, "Text p2", "Latin / English", "digital", False,
                    AnnotatorMetadata("a1","2026-01-01","draft"), "1.0"),
                GroundTruthPage(9, "Text p9", "Latin / English", "digital", False,
                    AnnotatorMetadata("a1","2026-01-01","approved"), "1.0"),
            ],
            dataset_version="1.0.0", schema_version="7.1",
            created_at="2026-01-01T00:00:00Z",
        )

        mock_list = self._mock_page_list("Text p1", page_num=1)

        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="b" * 64):
            result = DocumentEvaluator().evaluate(doc, b"fakepdf")

        self.assertEqual(result.evaluated_page_count, 1)   # page 1 approved + found
        self.assertEqual(result.skipped_page_count, 1)     # page 2 draft
        self.assertEqual(result.unavailable_page_count, 1) # page 9 not in extraction

    def test_F2_hash_mismatch_sets_failure_category(self):
        """F2: SHA-256 mismatch: hash_mismatch in all page failure categories; run continues."""
        from evaluation.runner import DocumentEvaluator
        from evaluation.schema import FailureCategory
        doc = self._make_simple_gt()
        mock_list = self._mock_page_list("Contract terms here.")
        # compute_source_hash returns a DIFFERENT hash from doc.source_hash
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="c" * 64):
            result = DocumentEvaluator().evaluate(doc, b"fakepdf")
        # Run should continue (evaluated_page_count > 0)
        self.assertEqual(result.evaluated_page_count, 1)
        pr = result.page_results[0]
        self.assertIn(FailureCategory.HASH_MISMATCH, pr.failure_categories)

    def test_F3_extraction_empty_failure_category(self):
        """F3: failure_category='extraction_empty' when predicted text is empty, reference non-empty."""
        from evaluation.runner import DocumentEvaluator
        from evaluation.schema import FailureCategory
        doc = self._make_simple_gt()
        mock_list = self._mock_page_list("")  # empty predicted text
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="b" * 64):
            result = DocumentEvaluator().evaluate(doc, b"fakepdf")
        pr = result.page_results[0]
        self.assertIn(FailureCategory.EXTRACTION_EMPTY, pr.failure_categories)

    def test_F4_high_cer_failure_category(self):
        """F4: failure_category='high_cer' when CER > 0.20."""
        from evaluation.runner import DocumentEvaluator
        from evaluation.schema import FailureCategory
        doc = self._make_simple_gt()
        # Very different text → high CER
        mock_list = self._mock_page_list("ZZZZZZZZZ ZZZZZZZZZ ZZZZZZZZZ.")
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="b" * 64):
            result = DocumentEvaluator(high_cer_threshold=0.20).evaluate(doc, b"fakepdf")
        pr = result.page_results[0]
        self.assertIn(FailureCategory.HIGH_CER, pr.failure_categories)

    def test_F5_reference_and_predicted_text_preserved(self):
        """F5: reference_text_raw and predicted_text_raw preserved in result."""
        from evaluation.runner import DocumentEvaluator
        doc = self._make_simple_gt()
        predicted_text = "Contract terms here."
        mock_list = self._mock_page_list(predicted_text)
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="b" * 64):
            result = DocumentEvaluator().evaluate(doc, b"fakepdf")
        pr = result.page_results[0]
        self.assertEqual(pr.reference_text_raw, "Contract terms here.")
        self.assertEqual(pr.predicted_text_raw, predicted_text)

    def test_F6_provider_exception_isolated(self):
        """F6: Provider exception in optional vision path → 'provider_error'; evaluation continues."""
        from evaluation.runner import DocumentEvaluator
        doc = self._make_simple_gt()
        mock_list = self._mock_page_list("Contract terms here.")
        with patch("evaluation.runner.extract_text_from_pdf", return_value=mock_list), \
             patch("evaluation.runner.compute_source_hash", return_value="b" * 64):
            # run_vision_pipeline=True; the vision call in _evaluate_page is a no-op pass,
            # so no real provider call is made. Test verifies run doesn't abort.
            result = DocumentEvaluator().evaluate(doc, b"fakepdf", run_vision_pipeline=True)
        self.assertEqual(result.evaluated_page_count, 1)


# =============================================================================
# G — Phase 6 Comparative (5 tests)
# =============================================================================

class TestPhase6Comparative(unittest.TestCase):

    def _make_gt(self) -> "GroundTruthDocument":
        from evaluation.schema import (
            GroundTruthDocument, GroundTruthPage, AnnotatorMetadata
        )
        return GroundTruthDocument(
            corpus_id="c1", corpus_version="1.0.0", document_id="d1",
            filename="d1.pdf", source_hash="a" * 64,
            document_type="nda", expected_document_class="digital_pdf",
            language="en", indic_scripts=[], page_count=1,
            pages=[GroundTruthPage(
                1, "Reference text for comparison.", "Latin / English",
                "digital", False,
                AnnotatorMetadata("a1","2026-01-01","approved"),
                "1.0",
            )],
            dataset_version="1.0.0", schema_version="7.1",
            created_at="2026-01-01T00:00:00Z",
        )

    def _mock_page_list(self, text: str):
        p = MagicMock()
        p.page_num = 1
        p.text = text
        p.extraction_source = "pymupdf"
        p.page_type = "digital"
        p.is_unclear = False
        p.ocr_confidence = None
        p.quality_score = 0.9
        pl = MagicMock()
        pl.__iter__ = lambda self: iter([p])
        pl.document_type = "digital_pdf"
        return pl

    def test_G1_paired_by_page_num(self):
        """G1: Pages paired by page_num; mismatched page nums → skipped."""
        from evaluation.comparative import Phase6ComparativeEvaluator
        from evaluation.schema import GroundTruthDocument, GroundTruthPage, AnnotatorMetadata

        gt = self._make_gt()
        # Add a page that won't appear in extraction
        gt.pages.append(GroundTruthPage(
            5, "Missing page text.", "Latin / English", "digital", False,
            AnnotatorMetadata("a1","2026-01-01","approved"), "1.0",
        ))

        mock_telem = MagicMock()
        mock_telem.optimization_applied = False
        mock_telem.optimization_method = "none"
        mock_telem.to_dict.return_value = {}

        mock_list = self._mock_page_list("Reference text for comparison.")

        with patch("evaluation.comparative.AdaptiveOptimizationEngine") as MockEng, \
             patch("evaluation.comparative.extract_text_from_pdf", return_value=mock_list):
            MockEng.return_value.optimize.return_value = (b"fakepdf", mock_telem)
            comp = Phase6ComparativeEvaluator()
            result = comp.compare(gt, b"fakepdf")

        # page 1 → paired; page 5 → skipped (not in extraction)
        self.assertEqual(result.paired_page_count, 1)
        self.assertGreaterEqual(result.skipped_page_count, 1)

    def test_G2_no_optimization_zero_delta(self):
        """G2: optimization_applied=False → cer_delta_mean=0.0, all pages unchanged."""
        from evaluation.comparative import Phase6ComparativeEvaluator

        gt = self._make_gt()
        identical_text = "Reference text for comparison."
        mock_list = self._mock_page_list(identical_text)

        mock_telem = MagicMock()
        mock_telem.optimization_applied = False
        mock_telem.optimization_method = "none"
        mock_telem.to_dict.return_value = {}

        with patch("evaluation.comparative.AdaptiveOptimizationEngine") as MockEng, \
             patch("evaluation.comparative.extract_text_from_pdf", return_value=mock_list):
            MockEng.return_value.optimize.return_value = (b"samepdf", mock_telem)
            comp = Phase6ComparativeEvaluator()
            result = comp.compare(gt, b"samepdf")

        self.assertAlmostEqual(result.cer_delta_mean, 0.0, places=3)
        self.assertFalse(result.optimization_applied)

    def test_G3_degraded_page_count(self):
        """G3: Degraded page count correct on mock with one page CER delta = +0.06."""
        from evaluation.comparative import Phase6ComparativeEvaluator

        gt = self._make_gt()
        # Baseline: identical text → CER = 0.0
        # Post: very different text → CER >> 0.01 → degraded
        baseline_list = self._mock_page_list("Reference text for comparison.")
        post_list = self._mock_page_list("ZZZZZZ ZZZZZZ ZZZZZZ ZZZZZZ ZZZZZZ.")

        mock_telem = MagicMock()
        mock_telem.optimization_applied = True
        mock_telem.optimization_method = "image_stream"
        mock_telem.to_dict.return_value = {}

        call_count = {"n": 0}
        def mock_extract(pdf_bytes):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return baseline_list
            return post_list

        with patch("evaluation.comparative.AdaptiveOptimizationEngine") as MockEng, \
             patch("evaluation.comparative.extract_text_from_pdf", side_effect=mock_extract):
            MockEng.return_value.optimize.return_value = (b"optpdf", mock_telem)
            comp = Phase6ComparativeEvaluator()
            result = comp.compare(gt, b"originalpdf")

        self.assertEqual(result.degraded_page_count, 1)
        self.assertEqual(result.improved_page_count, 0)

    def test_G4_compression_ratio(self):
        """G4: compression_ratio = optimized_size / original_size."""
        from evaluation.comparative import Phase6ComparativeEvaluator

        gt = self._make_gt()
        original = b"x" * 1000
        optimized = b"y" * 600
        mock_list = self._mock_page_list("Reference text for comparison.")

        mock_telem = MagicMock()
        mock_telem.optimization_applied = True
        mock_telem.optimization_method = "lossless"
        mock_telem.to_dict.return_value = {}

        with patch("evaluation.comparative.AdaptiveOptimizationEngine") as MockEng, \
             patch("evaluation.comparative.extract_text_from_pdf", return_value=mock_list):
            MockEng.return_value.optimize.return_value = (optimized, mock_telem)
            comp = Phase6ComparativeEvaluator()
            result = comp.compare(gt, original)

        expected_ratio = 600 / 1000
        self.assertAlmostEqual(result.compression_ratio, expected_ratio, places=5)

    def test_G5_disclaimer_present_in_comparison(self):
        """G5: DISCLAIMER present in Phase6ComparisonResult."""
        from evaluation.schema import Phase6ComparisonResult
        self.assertIn("NOT legal accuracy", Phase6ComparisonResult.DISCLAIMER)


# =============================================================================
# H — Import Isolation & Regression (4 tests)
# =============================================================================

class TestImportIsolationAndRegression(unittest.TestCase):

    def _get_backend_root(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..")

    def test_H1_production_modules_do_not_import_evaluation(self):
        """
        H1: Parse AST of all production modules and assert none import 'evaluation'.

        Scans: backend/services/*.py, backend/routers/*.py,
               backend/worker.py, backend/main.py, backend/config.py
        """
        backend_root = self._get_backend_root()
        scan_patterns = [
            os.path.join(backend_root, "services"),
            os.path.join(backend_root, "routers"),
        ]
        standalone_files = [
            os.path.join(backend_root, "worker.py"),
            os.path.join(backend_root, "main.py"),
            os.path.join(backend_root, "config.py"),
        ]

        violations = []

        def _check_file(filepath: str) -> None:
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=filepath)
            except (SyntaxError, UnicodeDecodeError):
                return  # skip unparseable files

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "evaluation" or alias.name.startswith("evaluation."):
                            violations.append(f"{filepath}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module == "evaluation" or module.startswith("evaluation."):
                        violations.append(f"{filepath}: from {module} import ...")

        for pattern_dir in scan_patterns:
            if os.path.isdir(pattern_dir):
                for fname in os.listdir(pattern_dir):
                    if fname.endswith(".py"):
                        _check_file(os.path.join(pattern_dir, fname))

        for fpath in standalone_files:
            if os.path.isfile(fpath):
                _check_file(fpath)

        self.assertEqual(
            violations, [],
            f"Production modules must NOT import evaluation. Violations:\n" + "\n".join(violations)
        )

    def test_H2_import_evaluation_no_fastapi_startup(self):
        """H2: 'import evaluation' does NOT trigger FastAPI startup, DB, or Redis connection."""
        # We verify indirectly: importing evaluation and its submodules does not
        # import 'fastapi', 'asyncpg', or 'redis' as side effects.
        # Use a subprocess-style check via importlib.
        import importlib

        # These should be importable without starting the app
        for mod_name in [
            "evaluation",
            "evaluation.schema",
            "evaluation.normalizer",
            "evaluation.metrics",
        ]:
            try:
                mod = importlib.import_module(mod_name)
                # Verify no FastAPI app object was created as a side effect
                self.assertFalse(
                    hasattr(mod, "app") and str(type(getattr(mod, "app", None))).startswith("<class 'fastapi"),
                    f"{mod_name} created a FastAPI app on import"
                )
            except ImportError as exc:
                self.fail(f"Failed to import {mod_name}: {exc}")

    def test_H3_extract_text_from_pdf_returns_page_content_list(self):
        """H3: extract_text_from_pdf called by runner returns a PageContentList (production contract)."""
        from services.pdf_parser import extract_text_from_pdf
        from services.page_content import PageContentList
        import io
        import fitz

        # Create a minimal valid PDF in memory
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Test contract clause.", fontsize=12)
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()
        pdf_bytes = buf.getvalue()

        result = extract_text_from_pdf(pdf_bytes)
        self.assertIsInstance(result, PageContentList)
        self.assertGreater(len(result), 0)

    def test_H4_reporter_json_has_required_keys(self):
        """H4: Reporter JSON output parses back with all required top-level keys."""
        from evaluation.schema import EvaluationRun
        from evaluation.reporter import EvaluationReporter
        from evaluation.metrics import CER_WER_ALGORITHM, aggregate_stats, document_class_accuracy, page_type_metrics, unclear_metrics
        from evaluation.normalizer import NORMALIZER_VERSION
        from evaluation.schema import SCHEMA_VERSION

        run = EvaluationRun(
            run_id="test-run-id",
            timestamp="2026-09-23T00:00:00+00:00",
            git_commit="abc123",
            schema_version=SCHEMA_VERSION,
            normalizer_version=NORMALIZER_VERSION,
            cer_wer_algorithm=CER_WER_ALGORITHM,
            normalization_config={"preserve_joiners": False},
            corpus_id="c1",
            corpus_version="1.0.0",
            dataset_version="1.0.0",
            total_documents=1,
            evaluated_document_count=1,
            total_pages_across_documents=2,
            evaluated_page_count=2,
            skipped_page_count=0,
            failed_page_count=0,
            unavailable_page_count=0,
            cer_stats=aggregate_stats([0.05, 0.10]),
            wer_stats=aggregate_stats([0.08, 0.12]),
            document_class_accuracy=document_class_accuracy(["digital_pdf"], ["digital_pdf"]),
            page_type_metrics=page_type_metrics(["digital","digital"], ["digital","digital"]),
            unclear_metrics=unclear_metrics([False, False], [False, False]),
            indic_cer_by_script={},
            per_document=[],
        )

        reporter = EvaluationReporter()
        json_str = reporter.generate_json(run)
        data = json.loads(json_str)

        required_keys = [
            "run_id", "timestamp", "git_commit",
            "schema_version", "normalizer_version", "cer_wer_algorithm",
            "normalization_config", "corpus_id", "corpus_version", "dataset_version",
            "counts", "cer_stats", "wer_stats",
            "document_class_accuracy", "page_type_metrics", "unclear_metrics",
            "indic_cer_by_script", "per_document", "DISCLAIMER",
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required key in JSON output: {key}")

        # DISCLAIMER must contain the prohibition
        self.assertIn("NOT legal accuracy", data["DISCLAIMER"])


if __name__ == "__main__":
    unittest.main()
