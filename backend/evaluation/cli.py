"""
cli.py — CLI Entry Point for Phase 7 Accuracy Evaluation Framework.

Usage:
    python -m evaluation.cli --dataset evaluation_datasets/ [OPTIONS]

Exit Codes:
    0 — SUCCESS: Evaluation completed; all thresholds met (or not set);
                 at least 1 page evaluated.
    1 — METRIC_THRESHOLD_EXCEEDED: Evaluation completed, but --cer-threshold
                 or --wer-threshold was exceeded.
    2 — INPUT_ERROR: Missing --dataset path, no .json files found,
                 unreadable/invalid JSON, or PDF not found.
    3 — PROVIDER_ERROR: --vision was passed, at least one vision provider
                 call failed, and ALL evaluated pages on the affected document
                 failed (no partial success possible on that document).
    4 — INSUFFICIENT_POPULATION: Dataset is structurally valid, but zero
                 pages reached review_state="approved"; no metrics computed.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_METRIC_THRESHOLD_EXCEEDED = 1
EXIT_INPUT_ERROR = 2
EXIT_PROVIDER_ERROR = 3
EXIT_INSUFFICIENT_POPULATION = 4


def _get_git_commit() -> str:
    """Capture current git commit hash; return 'unknown' on failure."""
    try:
        result = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return result.decode("utf-8").strip()
    except Exception:
        return "unknown"


def _load_gt_documents(dataset_dir: str) -> List:
    """Load all GroundTruthDocument JSON files from dataset_dir."""
    from evaluation.schema import GroundTruthDocument

    if not os.path.isdir(dataset_dir):
        logger.error("Dataset directory not found: %s", dataset_dir)
        sys.exit(EXIT_INPUT_ERROR)

    json_files = [
        os.path.join(dataset_dir, f)
        for f in os.listdir(dataset_dir)
        if f.endswith("_gt.json") or f.endswith(".json")
    ]

    if not json_files:
        logger.error("No ground-truth JSON files found in: %s", dataset_dir)
        sys.exit(EXIT_INPUT_ERROR)

    docs = []
    for path in sorted(json_files):
        try:
            doc = GroundTruthDocument.load_from_file(path)
            docs.append((path, doc))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("Failed to load ground-truth file %s: %s", path, exc)
            sys.exit(EXIT_INPUT_ERROR)

    return docs


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m evaluation.cli",
        description="SmartLegal-AI Phase 7 Accuracy Evaluation CLI",
    )
    parser.add_argument(
        "--dataset", required=False,
        help="Path to evaluation_datasets/ directory",
    )
    parser.add_argument("--output", help="Write JSON EvaluationRun to file (default: stdout)")
    parser.add_argument("--report", help="Write Markdown summary to file (optional)")
    parser.add_argument("--vision", action="store_true",
                        help="Enable optional Vision/OCR pipeline steps (requires API keys)")
    parser.add_argument("--compare-optimizer", action="store_true",
                        help="Run Phase 6 paired before/after comparison")
    parser.add_argument("--filter-script",
                        help="Evaluate only documents containing this Indic script")
    parser.add_argument("--cer-threshold", type=float,
                        help="Exit code 1 if overall mean CER > threshold")
    parser.add_argument("--wer-threshold", type=float,
                        help="Exit code 1 if overall mean WER > threshold")
    parser.add_argument("--preserve-joiners", action="store_true",
                        help="Retain ZWJ/ZWNJ during normalization")
    parser.add_argument("--version", action="store_true",
                        help="Print version metadata and exit 0")

    args = parser.parse_args(argv)

    # --version
    if args.version:
        from evaluation.schema import SCHEMA_VERSION
        from evaluation.normalizer import NORMALIZER_VERSION
        from evaluation.metrics import CER_WER_ALGORITHM
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "normalizer_version": NORMALIZER_VERSION,
            "cer_wer_algorithm": CER_WER_ALGORITHM,
        }, indent=2))
        sys.exit(EXIT_SUCCESS)

    if not args.dataset:
        parser.print_help()
        sys.exit(EXIT_INPUT_ERROR)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from evaluation.schema import (
        SCHEMA_VERSION,
        EvaluationRun,
        GroundTruthDocument,
    )
    from evaluation.normalizer import NORMALIZER_VERSION
    from evaluation.metrics import (
        CER_WER_ALGORITHM,
        aggregate_stats,
        document_class_accuracy,
        page_type_metrics,
        unclear_metrics,
    )
    from evaluation.runner import DocumentEvaluator
    from evaluation.reporter import EvaluationReporter

    preserve_joiners = bool(args.preserve_joiners)

    # Load ground-truth documents (no PDF files needed yet)
    doc_entries = _load_gt_documents(args.dataset)

    # Apply script filter
    if args.filter_script:
        doc_entries = [
            (path, doc) for path, doc in doc_entries
            if args.filter_script in doc.indic_scripts
        ]
        if not doc_entries:
            logger.error("No documents match --filter-script=%s", args.filter_script)
            sys.exit(EXIT_INPUT_ERROR)

    evaluator = DocumentEvaluator(preserve_joiners=preserve_joiners)
    reporter = EvaluationReporter()

    all_doc_results = []
    all_cer_values: List[float] = []
    all_wer_values: List[float] = []
    predicted_classes: List[str] = []
    expected_classes: List[str] = []
    predicted_page_types: List[str] = []
    expected_page_types: List[str] = []
    predicted_unclear: List[bool] = []
    expected_unclear: List[bool] = []
    indic_cer_map: dict = {}

    total_evaluated = 0
    total_skipped = 0
    total_failed = 0
    total_unavailable = 0
    total_pages = 0
    provider_error_docs = 0

    corpus_id = ""
    corpus_version = ""
    dataset_versions: List[str] = []

    for path, gt_doc in doc_entries:
        corpus_id = gt_doc.corpus_id
        corpus_version = gt_doc.corpus_version
        dataset_versions.append(gt_doc.dataset_version)

        # Find the corresponding PDF
        # Convention: same directory as the _gt.json file, filename = gt_doc.filename
        pdf_path = os.path.join(os.path.dirname(path), gt_doc.filename)
        if not os.path.isfile(pdf_path):
            # Try looking in dataset dir directly
            pdf_path = os.path.join(args.dataset, gt_doc.filename)

        if not os.path.isfile(pdf_path):
            logger.warning(
                "PDF not found for doc_id=%s (expected: %s); skipping.",
                gt_doc.document_id, gt_doc.filename,
            )
            continue

        with open(pdf_path, "rb") as fh:
            pdf_bytes = fh.read()

        doc_result = evaluator.evaluate(
            gt_doc, pdf_bytes, run_vision_pipeline=bool(args.vision)
        )
        all_doc_results.append(doc_result)
        total_pages += gt_doc.page_count
        total_evaluated += doc_result.evaluated_page_count
        total_skipped += doc_result.skipped_page_count
        total_failed += doc_result.failed_page_count
        total_unavailable += doc_result.unavailable_page_count

        if doc_result.cer_stats.get("mean") is not None:
            predicted_classes.append(doc_result.predicted_document_class)
            expected_classes.append(doc_result.expected_document_class)

        for pr in doc_result.page_results:
            if pr.review_state == "approved" and pr.cer is not None:
                all_cer_values.append(pr.cer)
            if pr.review_state == "approved" and pr.wer is not None:
                all_wer_values.append(pr.wer)
            if pr.predicted_page_type is not None:
                predicted_page_types.append(pr.predicted_page_type)
                expected_page_types.append(pr.expected_page_type)
            if pr.predicted_is_unclear is not None:
                predicted_unclear.append(pr.predicted_is_unclear)
                expected_unclear.append(pr.expected_is_unclear)

        # Indic script CER aggregation
        for script in gt_doc.indic_scripts:
            for pr in doc_result.page_results:
                if pr.review_state == "approved" and pr.cer is not None:
                    indic_cer_map.setdefault(script, []).append(pr.cer)

        # Check for all-failed provider errors (only relevant when --vision)
        if args.vision and doc_result.failed_page_count == doc_result.evaluated_page_count + doc_result.failed_page_count > 0:
            provider_error_docs += 1

    # ------------------------------------------------------------------
    # Insufficient population check
    # ------------------------------------------------------------------
    if total_evaluated == 0:
        print(json.dumps({
            "error": "insufficient_population",
            "message": "Zero approved pages were evaluated. No metrics computed.",
            "total_documents": len(doc_entries),
            "total_skipped": total_skipped,
        }))
        sys.exit(EXIT_INSUFFICIENT_POPULATION)

    # ------------------------------------------------------------------
    # Global aggregation
    # ------------------------------------------------------------------
    global_cer = aggregate_stats(all_cer_values, label="global_cer")
    global_wer = aggregate_stats(all_wer_values, label="global_wer")
    doc_class_acc = document_class_accuracy(predicted_classes, expected_classes)
    pt_metrics = page_type_metrics(predicted_page_types, expected_page_types)
    ul_metrics = unclear_metrics(predicted_unclear, expected_unclear)

    indic_cer_by_script = {
        script: {"cer_stats": aggregate_stats(vals, label=script)}
        for script, vals in indic_cer_map.items()
    }

    dataset_version = min(dataset_versions) if dataset_versions else "unknown"

    run = EvaluationRun(
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        git_commit=_get_git_commit(),
        schema_version=SCHEMA_VERSION,
        normalizer_version=NORMALIZER_VERSION,
        cer_wer_algorithm=CER_WER_ALGORITHM,
        normalization_config={"preserve_joiners": preserve_joiners},
        corpus_id=corpus_id,
        corpus_version=corpus_version,
        dataset_version=dataset_version,
        total_documents=len(doc_entries),
        evaluated_document_count=len(all_doc_results),
        total_pages_across_documents=total_pages,
        evaluated_page_count=total_evaluated,
        skipped_page_count=total_skipped,
        failed_page_count=total_failed,
        unavailable_page_count=total_unavailable,
        cer_stats=global_cer,
        wer_stats=global_wer,
        document_class_accuracy=doc_class_acc,
        page_type_metrics=pt_metrics,
        unclear_metrics=ul_metrics,
        indic_cer_by_script=indic_cer_by_script,
        per_document=all_doc_results,
    )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    json_output = reporter.generate_json(run)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(json_output)
    else:
        print(json_output)

    if args.report:
        md_output = reporter.generate_markdown(run)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(md_output)

    # ------------------------------------------------------------------
    # Exit code determination
    # ------------------------------------------------------------------
    if args.vision and provider_error_docs > 0 and total_evaluated == 0:
        sys.exit(EXIT_PROVIDER_ERROR)

    mean_cer = global_cer.get("mean")
    mean_wer = global_wer.get("mean")

    if args.cer_threshold is not None and mean_cer is not None:
        if mean_cer > args.cer_threshold:
            sys.exit(EXIT_METRIC_THRESHOLD_EXCEEDED)

    if args.wer_threshold is not None and mean_wer is not None:
        if mean_wer > args.wer_threshold:
            sys.exit(EXIT_METRIC_THRESHOLD_EXCEEDED)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
