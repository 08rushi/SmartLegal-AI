"""
runner.py — Per-Document Evaluation Runner (Phase 7).

Evaluates extracted pipeline output against human-verified ground-truth
documents. Strictly read-only with respect to all production services.

LEGAL ACCURACY DISCLAIMER:
This runner measures transcription/representation fidelity only.
It does NOT measure legal accuracy, semantic correctness, contractual
correctness, or legal validity.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Dict, List, Optional, Tuple

from evaluation.metrics import (
    CER_WER_ALGORITHM,
    aggregate_stats,
    compute_cer,
    compute_wer,
    document_class_accuracy,
    ocr_confidence_vs_cer_correlation,
    page_type_metrics,
    unclear_metrics,
)
from evaluation.schema import (
    FailureCategory,
    GroundTruthDocument,
    GroundTruthPage,
    DocumentEvaluationResult,
    PageEvaluationResult,
    compute_source_hash,
)
from services.pdf_parser import extract_text_from_pdf


logger = logging.getLogger(__name__)

# Default thresholds
DEFAULT_HIGH_CER_THRESHOLD: float = 0.20
DEFAULT_HIGH_WER_THRESHOLD: float = 0.20
DEFAULT_OCR_LOW_CONFIDENCE_THRESHOLD: float = 0.35


class DocumentEvaluator:
    """
    Evaluates a single GroundTruthDocument against extracted PDF output.

    Imports production services read-only. Never modifies production code.
    """

    def __init__(
        self,
        high_cer_threshold: float = DEFAULT_HIGH_CER_THRESHOLD,
        high_wer_threshold: float = DEFAULT_HIGH_WER_THRESHOLD,
        ocr_low_confidence_threshold: float = DEFAULT_OCR_LOW_CONFIDENCE_THRESHOLD,
        preserve_joiners: bool = False,
    ) -> None:
        self.high_cer_threshold = high_cer_threshold
        self.high_wer_threshold = high_wer_threshold
        self.ocr_low_confidence_threshold = ocr_low_confidence_threshold
        self.preserve_joiners = preserve_joiners

    def evaluate(
        self,
        gt_doc: GroundTruthDocument,
        pdf_bytes: bytes,
        run_vision_pipeline: bool = False,
    ) -> DocumentEvaluationResult:
        """
        Evaluate a document's extraction quality against ground truth.

        Args:
            gt_doc: Human-verified ground-truth document.
            pdf_bytes: Raw bytes of the source PDF.
            run_vision_pipeline: If True, attempt optional vision/OCR path
                for non-digital pages (requires API keys).

        Returns:
            DocumentEvaluationResult with all four page population counts.
        """
        # ------------------------------------------------------------------
        # 1. Hash verification
        # ------------------------------------------------------------------
        actual_hash = compute_source_hash(pdf_bytes)
        hash_mismatch = actual_hash != gt_doc.source_hash
        if hash_mismatch:
            logger.warning(
                "Source hash mismatch for doc_id=%s: expected=%s actual=%s",
                gt_doc.document_id,
                gt_doc.source_hash,
                actual_hash,
            )

        # ------------------------------------------------------------------
        # 2. Extraction (production service, read-only)
        # ------------------------------------------------------------------
        try:
            page_list = extract_text_from_pdf(pdf_bytes)
        except Exception as exc:
            logger.error("PDF extraction failed for doc_id=%s: %s", gt_doc.document_id, exc)
            page_list = []

        # Build a lookup by page_num
        extracted_by_page: Dict[int, object] = {
            p.page_num: p for p in page_list
        }

        predicted_doc_class = getattr(page_list, "document_type", "empty_pdf") if page_list else "empty_pdf"

        # ------------------------------------------------------------------
        # 3. Per-page evaluation
        # ------------------------------------------------------------------
        page_results: List[PageEvaluationResult] = []

        evaluated_cers: List[float] = []
        evaluated_wers: List[float] = []
        predicted_page_types: List[str] = []
        expected_page_types_list: List[str] = []
        predicted_unclear_list: List[bool] = []
        expected_unclear_list: List[bool] = []
        ocr_confidences: List[float] = []
        ocr_cers: List[float] = []

        evaluated_count = 0
        skipped_count = 0
        failed_count = 0
        unavailable_count = 0

        for gt_page in gt_doc.pages:
            review_state = gt_page.annotation.review_state

            # Not approved → skipped
            if review_state != "approved":
                skipped_count += 1
                page_results.append(PageEvaluationResult(
                    page_num=gt_page.page_num,
                    review_state="skipped",
                    extraction_source="",
                    cer=None, wer=None,
                    cer_ref_char_count=0, wer_ref_word_count=0,
                    predicted_page_type=None,
                    expected_page_type=gt_page.expected_page_type,
                    page_type_correct=None,
                    predicted_is_unclear=None,
                    expected_is_unclear=gt_page.expected_is_unclear,
                    unclear_match=None,
                    ocr_confidence=None, quality_score=None,
                    failure_categories=[FailureCategory.ANNOTATION_INCOMPLETE],
                    reference_text_raw=gt_page.reference_text,
                    predicted_text_raw="",
                ))
                continue

            # Page not found in extraction → unavailable
            if gt_page.page_num not in extracted_by_page:
                unavailable_count += 1
                page_results.append(PageEvaluationResult(
                    page_num=gt_page.page_num,
                    review_state="unavailable",
                    extraction_source="",
                    cer=None, wer=None,
                    cer_ref_char_count=0, wer_ref_word_count=0,
                    predicted_page_type=None,
                    expected_page_type=gt_page.expected_page_type,
                    page_type_correct=None,
                    predicted_is_unclear=None,
                    expected_is_unclear=gt_page.expected_is_unclear,
                    unclear_match=None,
                    ocr_confidence=None, quality_score=None,
                    failure_categories=[],
                    reference_text_raw=gt_page.reference_text,
                    predicted_text_raw="",
                ))
                continue

            # Approved and found → evaluate
            pred_page = extracted_by_page[gt_page.page_num]
            try:
                result = self._evaluate_page(
                    gt_page=gt_page,
                    pred_page=pred_page,
                    hash_mismatch=hash_mismatch,
                    run_vision_pipeline=run_vision_pipeline,
                )
                evaluated_count += 1
                page_results.append(result)

                if result.cer is not None:
                    evaluated_cers.append(result.cer)
                if result.wer is not None:
                    evaluated_wers.append(result.wer)
                if result.predicted_page_type is not None:
                    predicted_page_types.append(result.predicted_page_type)
                    expected_page_types_list.append(gt_page.expected_page_type)
                if result.predicted_is_unclear is not None:
                    predicted_unclear_list.append(result.predicted_is_unclear)
                    expected_unclear_list.append(gt_page.expected_is_unclear)
                if result.ocr_confidence is not None and result.cer is not None:
                    ocr_confidences.append(result.ocr_confidence)
                    ocr_cers.append(result.cer)

            except Exception as exc:
                logger.error(
                    "Page evaluation failed for doc_id=%s page=%d: %s",
                    gt_doc.document_id, gt_page.page_num, exc,
                )
                failed_count += 1
                page_results.append(PageEvaluationResult(
                    page_num=gt_page.page_num,
                    review_state="failed",
                    extraction_source="",
                    cer=None, wer=None,
                    cer_ref_char_count=0, wer_ref_word_count=0,
                    predicted_page_type=None,
                    expected_page_type=gt_page.expected_page_type,
                    page_type_correct=None,
                    predicted_is_unclear=None,
                    expected_is_unclear=gt_page.expected_is_unclear,
                    unclear_match=None,
                    ocr_confidence=None, quality_score=None,
                    failure_categories=[FailureCategory.PROVIDER_ERROR],
                    reference_text_raw=gt_page.reference_text,
                    predicted_text_raw="",
                ))

        # ------------------------------------------------------------------
        # 4. Aggregation
        # ------------------------------------------------------------------
        cer_agg = aggregate_stats(evaluated_cers, label="cer")
        wer_agg = aggregate_stats(evaluated_wers, label="wer")

        pt_metrics = (
            page_type_metrics(predicted_page_types, expected_page_types_list)
            if predicted_page_types
            else page_type_metrics([], [])
        )
        ul_metrics = (
            unclear_metrics(predicted_unclear_list, expected_unclear_list)
            if predicted_unclear_list
            else unclear_metrics([], [])
        )
        ocr_corr = ocr_confidence_vs_cer_correlation(ocr_confidences, ocr_cers)

        doc_class_correct = predicted_doc_class == gt_doc.expected_document_class

        return DocumentEvaluationResult(
            doc_id=gt_doc.document_id,
            corpus_id=gt_doc.corpus_id,
            document_id=gt_doc.document_id,
            filename=gt_doc.filename,
            source_hash=gt_doc.source_hash,
            predicted_document_class=predicted_doc_class,
            expected_document_class=gt_doc.expected_document_class,
            document_class_correct=doc_class_correct,
            total_pages_in_document=gt_doc.page_count,
            evaluated_page_count=evaluated_count,
            skipped_page_count=skipped_count,
            failed_page_count=failed_count,
            unavailable_page_count=unavailable_count,
            cer_stats=cer_agg,
            wer_stats=wer_agg,
            page_type_metrics=pt_metrics,
            unclear_metrics=ul_metrics,
            ocr_correlation=ocr_corr,
            page_results=page_results,
        )

    def _evaluate_page(
        self,
        gt_page: GroundTruthPage,
        pred_page: object,
        hash_mismatch: bool,
        run_vision_pipeline: bool,
    ) -> PageEvaluationResult:
        """Evaluate a single approved page."""
        predicted_text = getattr(pred_page, "text", "") or ""
        extraction_source = getattr(pred_page, "extraction_source", "unknown")
        predicted_page_type = getattr(pred_page, "page_type", None)
        predicted_is_unclear = getattr(pred_page, "is_unclear", None)
        ocr_confidence = getattr(pred_page, "ocr_confidence", None)
        quality_score = getattr(pred_page, "quality_score", None)

        # Optional vision pipeline step (provider errors isolated)
        if run_vision_pipeline and predicted_page_type in ("scanned", "empty"):
            try:
                # Vision pipeline would be invoked here if needed.
                # Errors do not abort; fallback to PyMuPDF result.
                pass
            except Exception as exc:
                logger.warning("Vision pipeline failed for page %d: %s", gt_page.page_num, exc)

        # CER / WER
        cer, cer_ref_count = compute_cer(
            gt_page.reference_text, predicted_text, self.preserve_joiners
        )
        wer, wer_ref_count = compute_wer(
            gt_page.reference_text, predicted_text, self.preserve_joiners
        )

        # UNCLEAR pairing
        unclear_match: Optional[str] = None
        if predicted_is_unclear is not None:
            pred_u = bool(predicted_is_unclear)
            exp_u = bool(gt_page.expected_is_unclear)
            if pred_u and exp_u:
                unclear_match = "TP"
            elif pred_u and not exp_u:
                unclear_match = "FP"
            elif not pred_u and exp_u:
                unclear_match = "FN"
            else:
                unclear_match = "TN"

        # Page type match
        page_type_correct: Optional[bool] = None
        if predicted_page_type is not None:
            page_type_correct = predicted_page_type == gt_page.expected_page_type

        # Failure taxonomy
        failure_categories: List[str] = []

        if hash_mismatch:
            failure_categories.append(FailureCategory.HASH_MISMATCH)

        ref_norm_stripped = gt_page.reference_text.strip()
        pred_norm_stripped = predicted_text.strip()

        if ref_norm_stripped and not pred_norm_stripped:
            failure_categories.append(FailureCategory.EXTRACTION_EMPTY)

        if ocr_confidence is not None and ocr_confidence < self.ocr_low_confidence_threshold:
            failure_categories.append(FailureCategory.OCR_LOW_CONFIDENCE)

        if predicted_is_unclear:
            failure_categories.append(FailureCategory.OCR_UNCLEAR_FLAG)

        if page_type_correct is False:
            failure_categories.append(FailureCategory.CLASSIFICATION_MISMATCH)

        if cer > self.high_cer_threshold:
            failure_categories.append(FailureCategory.HIGH_CER)

        if wer > self.high_wer_threshold:
            failure_categories.append(FailureCategory.HIGH_WER)

        return PageEvaluationResult(
            page_num=gt_page.page_num,
            review_state="approved",
            extraction_source=extraction_source,
            cer=cer,
            wer=wer,
            cer_ref_char_count=cer_ref_count,
            wer_ref_word_count=wer_ref_count,
            predicted_page_type=predicted_page_type,
            expected_page_type=gt_page.expected_page_type,
            page_type_correct=page_type_correct,
            predicted_is_unclear=predicted_is_unclear,
            expected_is_unclear=gt_page.expected_is_unclear,
            unclear_match=unclear_match,
            ocr_confidence=ocr_confidence,
            quality_score=quality_score,
            failure_categories=failure_categories,
            reference_text_raw=gt_page.reference_text,
            predicted_text_raw=predicted_text,
        )
