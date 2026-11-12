"""
comparative.py — Phase 6 Paired Before/After Optimization Comparison (Phase 7).

Evaluates the impact of adaptive document optimization on transcription fidelity.
Pairing is enforced at corpus + document + page level.

LEGAL ACCURACY DISCLAIMER:
CER/WER deltas measure transcription fidelity change due to optimization only.
They do NOT measure legal accuracy, semantic correctness, contractual
correctness, or legal validity.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from evaluation.metrics import (
    aggregate_stats,
    compute_cer,
    compute_wer,
)
from evaluation.runner import DocumentEvaluator
from evaluation.schema import (
    FailureCategory,
    GroundTruthDocument,
    Phase6ComparisonResult,
)
from services.adaptive_optimizer import AdaptiveOptimizationEngine
from services.pdf_parser import extract_text_from_pdf


logger = logging.getLogger(__name__)

# Improvement/degradation thresholds (reporting classification only —
# NOT quality gates that block processing).
IMPROVE_THRESHOLD: float = -0.01   # cer_after - cer_before < -0.01 → improved
DEGRADE_THRESHOLD: float = 0.01    # cer_after - cer_before >  0.01 → degraded


class Phase6ComparativeEvaluator:
    """
    Evaluates Phase 6 adaptive optimization impact on transcription fidelity.

    Pairing contract:
      1. Corpus level  — same corpus_id + corpus_version
      2. Document level — same document_id + source_hash
      3. Page level    — same page_num with same reference_text

    A page pair is valid only if:
      - review_state == "approved" on the ground-truth page
      - Both pre-optimization and post-optimization page extractions succeeded
    """

    def __init__(self, preserve_joiners: bool = False) -> None:
        self.preserve_joiners = preserve_joiners
        self._evaluator = DocumentEvaluator(preserve_joiners=preserve_joiners)

    def compare(
        self,
        gt_doc: GroundTruthDocument,
        original_pdf_bytes: bytes,
        filename: str = "",
    ) -> Phase6ComparisonResult:
        """
        Run paired before/after comparison for a document.

        Args:
            gt_doc: Ground-truth document (must match source_hash of original_pdf_bytes).
            original_pdf_bytes: Raw bytes of the original (pre-optimization) PDF.
            filename: Optional filename passed to the optimizer for strategy selection.

        Returns:
            Phase6ComparisonResult with paired CER/WER deltas.
        """
        orig_size = len(original_pdf_bytes)

        # ------------------------------------------------------------------
        # Run optimizer (production service, read-only call)
        # ------------------------------------------------------------------
        try:
            engine = AdaptiveOptimizationEngine()
            optimized_bytes, telemetry = engine.optimize(original_pdf_bytes, filename)
        except Exception as exc:
            logger.error(
                "Optimizer failed for doc_id=%s: %s — using original bytes as both sides.",
                gt_doc.document_id, exc,
            )
            optimized_bytes = original_pdf_bytes
            telemetry = None

        opt_size = len(optimized_bytes)
        compression_ratio = opt_size / orig_size if orig_size > 0 else 1.0

        optimization_applied = (
            telemetry.optimization_applied if telemetry is not None else False
        )
        optimization_method = (
            telemetry.optimization_method if telemetry is not None else "none"
        )
        telemetry_dict = telemetry.to_dict() if telemetry is not None else {}

        # ------------------------------------------------------------------
        # Extract text from both sides
        # ------------------------------------------------------------------
        try:
            baseline_pages = extract_text_from_pdf(original_pdf_bytes)
        except Exception as exc:
            logger.error("Baseline extraction failed: %s", exc)
            baseline_pages = []

        try:
            post_pages = extract_text_from_pdf(optimized_bytes)
        except Exception as exc:
            logger.error("Post-optimization extraction failed: %s", exc)
            post_pages = []

        baseline_by_num = {p.page_num: p for p in baseline_pages}
        post_by_num = {p.page_num: p for p in post_pages}

        # ------------------------------------------------------------------
        # Paired page evaluation
        # ------------------------------------------------------------------
        paired_cers_baseline: List[float] = []
        paired_cers_post: List[float] = []
        paired_wers_baseline: List[float] = []
        paired_wers_post: List[float] = []

        improved = unchanged = degraded = skipped = failed = 0

        for gt_page in gt_doc.pages:
            if gt_page.annotation.review_state != "approved":
                skipped += 1
                continue

            if gt_page.page_num not in baseline_by_num or gt_page.page_num not in post_by_num:
                skipped += 1
                continue

            try:
                ref_text = gt_page.reference_text
                base_text = getattr(baseline_by_num[gt_page.page_num], "text", "") or ""
                post_text = getattr(post_by_num[gt_page.page_num], "text", "") or ""

                cer_base, _ = compute_cer(ref_text, base_text, self.preserve_joiners)
                cer_post, _ = compute_cer(ref_text, post_text, self.preserve_joiners)
                wer_base, _ = compute_wer(ref_text, base_text, self.preserve_joiners)
                wer_post, _ = compute_wer(ref_text, post_text, self.preserve_joiners)

                paired_cers_baseline.append(cer_base)
                paired_cers_post.append(cer_post)
                paired_wers_baseline.append(wer_base)
                paired_wers_post.append(wer_post)

                cer_delta = cer_post - cer_base
                if cer_delta < IMPROVE_THRESHOLD:
                    improved += 1
                elif cer_delta > DEGRADE_THRESHOLD:
                    degraded += 1
                else:
                    unchanged += 1

            except Exception as exc:
                logger.error(
                    "Paired page evaluation failed doc_id=%s page=%d: %s",
                    gt_doc.document_id, gt_page.page_num, exc,
                )
                failed += 1

        paired_count = improved + unchanged + degraded

        # ------------------------------------------------------------------
        # Aggregate stats
        # ------------------------------------------------------------------
        baseline_cer_agg = aggregate_stats(paired_cers_baseline, label="baseline_cer")
        post_cer_agg = aggregate_stats(paired_cers_post, label="post_cer")
        baseline_wer_agg = aggregate_stats(paired_wers_baseline, label="baseline_wer")
        post_wer_agg = aggregate_stats(paired_wers_post, label="post_wer")

        baseline_mean = baseline_cer_agg.get("mean") or 0.0
        post_mean = post_cer_agg.get("mean") or 0.0
        cer_delta_mean = post_mean - baseline_mean

        baseline_wer_mean = baseline_wer_agg.get("mean") or 0.0
        post_wer_mean = post_wer_agg.get("mean") or 0.0
        wer_delta_mean = post_wer_mean - baseline_wer_mean

        return Phase6ComparisonResult(
            doc_id=gt_doc.document_id,
            corpus_id=gt_doc.corpus_id,
            document_id=gt_doc.document_id,
            source_hash=gt_doc.source_hash,
            filename=gt_doc.filename,
            optimization_applied=optimization_applied,
            optimization_method=optimization_method,
            original_size_bytes=orig_size,
            optimized_size_bytes=opt_size,
            compression_ratio=compression_ratio,
            baseline_cer_stats=baseline_cer_agg,
            post_cer_stats=post_cer_agg,
            cer_delta_mean=cer_delta_mean,
            baseline_wer_stats=baseline_wer_agg,
            post_wer_stats=post_wer_agg,
            wer_delta_mean=wer_delta_mean,
            paired_page_count=paired_count,
            improved_page_count=improved,
            unchanged_page_count=unchanged,
            degraded_page_count=degraded,
            skipped_page_count=skipped,
            failed_page_count=failed,
            telemetry=telemetry_dict,
        )
