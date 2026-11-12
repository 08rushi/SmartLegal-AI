"""
reporter.py — JSON and Markdown Aggregate Report Generation (Phase 7).

Generates machine-readable JSON and human-readable Markdown summaries
from EvaluationRun results.

LEGAL ACCURACY DISCLAIMER:
All reported metrics measure transcription/representation fidelity only.
They do NOT measure legal accuracy, semantic correctness, contractual
correctness, or legal validity.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from evaluation.schema import EvaluationRun


_DISCLAIMER = (
    "All metrics measure transcription/representation fidelity only. "
    "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
)


class EvaluationReporter:
    """
    Generates JSON and Markdown reports from an EvaluationRun.

    The JSON output is a complete serialization of EvaluationRun.
    The Markdown output includes all 12 required sections from Plan v1.1.
    """

    def generate_json(self, run: EvaluationRun) -> str:
        """Serialize EvaluationRun to indented JSON string."""
        return json.dumps(run.to_dict(), ensure_ascii=False, indent=2)

    def generate_markdown(self, run: EvaluationRun) -> str:
        """Generate human-readable Markdown summary with all 12 required sections."""
        lines: List[str] = []

        # 1. Disclaimer block (top)
        lines += [
            "# SmartLegal-AI — Phase 7 Accuracy Evaluation Report",
            "",
            "> **DISCLAIMER**: " + _DISCLAIMER,
            "",
        ]

        # 2. Run metadata
        lines += [
            "## 1. Run Metadata",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Run ID | `{run.run_id}` |",
            f"| Timestamp | {run.timestamp} |",
            f"| Git Commit | `{run.git_commit}` |",
            f"| Schema Version | {run.schema_version} |",
            f"| Normalizer Version | {run.normalizer_version} |",
            f"| CER/WER Algorithm | {run.cer_wer_algorithm} |",
            f"| Preserve Joiners | {run.normalization_config.get('preserve_joiners', False)} |",
            "",
        ]

        # 3. Dataset / corpus summary
        counts = run.to_dict()["counts"]
        lines += [
            "## 2. Dataset / Corpus Summary",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Corpus ID | {run.corpus_id} |",
            f"| Corpus Version | {run.corpus_version} |",
            f"| Dataset Version | {run.dataset_version} |",
            f"| Total Documents | {counts['total_documents']} |",
            f"| Evaluated Documents | {counts['evaluated_documents']} |",
            f"| Total Pages | {counts['total_pages']} |",
            f"| Evaluated Pages | {counts['evaluated_pages']} |",
            f"| Skipped Pages | {counts['skipped_pages']} |",
            f"| Failed Pages | {counts['failed_pages']} |",
            f"| Unavailable Pages | {counts['unavailable_pages']} |",
            "",
        ]

        # 4. CER/WER summary
        def _fmt_stats(stats: Dict) -> List[str]:
            if stats.get("insufficient_data"):
                return [f"| Sample Count | {stats.get('sample_count', 0)} |",
                        "| Status | Insufficient data |"]
            return [
                f"| Sample Count | {stats['sample_count']} |",
                f"| Mean | {stats['mean']:.4f} |",
                f"| Median | {stats['median']:.4f} |",
                f"| P95 | {stats['p95']:.4f} |",
                f"| Min | {stats['min']:.4f} |",
                f"| Max | {stats['max']:.4f} |",
                f"| Std Dev | {stats['std_dev']:.4f} |",
            ]

        lines += [
            "## 3. CER / WER Summary",
            "",
            "### Character Error Rate (CER)",
            "",
            "| Metric | Value |",
            "|---|---|",
        ]
        lines += _fmt_stats(run.cer_stats)
        lines += [
            "",
            "### Word Error Rate (WER)",
            "",
            "| Metric | Value |",
            "|---|---|",
        ]
        lines += _fmt_stats(run.wer_stats)
        lines.append("")

        # 5. Document class accuracy
        dca = run.document_class_accuracy
        acc_str = f"{dca['accuracy']:.4f}" if dca.get("accuracy") is not None else "N/A"
        lines += [
            "## 4. Document Class Accuracy",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Correct | {dca.get('correct', 0)} |",
            f"| Total | {dca.get('total', 0)} |",
            f"| Accuracy | {acc_str} |",
            "",
        ]

        # 6. Page type metrics
        lines += [
            "## 5. Page Type Classification Metrics (Per-Class)",
            "",
            "| Class | Precision | Recall | F1 | Support |",
            "|---|---|---|---|---|",
        ]
        pt = run.page_type_metrics.get("per_class", {})
        for cls, vals in pt.items():
            def _fmt(v: Any) -> str:
                return f"{v:.4f}" if v is not None else "N/A"
            lines.append(
                f"| {cls} | {_fmt(vals.get('precision'))} | "
                f"{_fmt(vals.get('recall'))} | {_fmt(vals.get('f1'))} | "
                f"{vals.get('support', 0)} |"
            )
        macro_f1 = run.page_type_metrics.get("macro_f1")
        lines += [
            "",
            f"**Macro F1**: {'N/A' if macro_f1 is None else f'{macro_f1:.4f}'}",
            f"**Sample Count**: {run.page_type_metrics.get('sample_count', 0)}",
            "",
        ]

        # 7. UNCLEAR metrics
        ul = run.unclear_metrics
        def _fmt_opt(v: Any) -> str:
            return f"{v:.4f}" if v is not None else "N/A"
        lines += [
            "## 6. UNCLEAR Detection Metrics",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| TP | {ul.get('tp', 0)} |",
            f"| FP | {ul.get('fp', 0)} |",
            f"| FN | {ul.get('fn', 0)} |",
            f"| TN | {ul.get('tn', 0)} |",
            f"| Precision | {_fmt_opt(ul.get('precision'))} |",
            f"| Recall | {_fmt_opt(ul.get('recall'))} |",
            f"| F1 | {_fmt_opt(ul.get('f1'))} |",
            f"| Support (expected UNCLEAR) | {ul.get('support', 0)} |",
            f"| Sample Count | {ul.get('sample_count', 0)} |",
            "",
        ]

        # 8. OCR confidence correlation — pulled from first document result that has it
        ocr_corr: Optional[Dict] = None
        for doc_res in run.per_document:
            if doc_res.ocr_correlation and doc_res.ocr_correlation.get("sample_count", 0) > 0:
                ocr_corr = doc_res.ocr_correlation
                break
        if ocr_corr:
            corr_val = ocr_corr.get("correlation")
            lines += [
                "## 7. OCR Confidence Correlation",
                "",
                "| Metric | Value |",
                "|---|---|",
                f"| Algorithm | {ocr_corr.get('algorithm', 'N/A')} |",
                f"| Sample Count | {ocr_corr.get('sample_count', 0)} |",
                f"| Correlation | {'N/A' if corr_val is None else f'{corr_val:.4f}'} |",
                f"| Insufficient Data | {ocr_corr.get('insufficient_data', True)} |",
                "",
            ]
        else:
            lines += ["## 7. OCR Confidence Correlation", "", "No OCR correlation data available.", ""]

        # 9. Indic script CER breakdown
        lines += ["## 8. Indic Script CER Breakdown", ""]
        if run.indic_cer_by_script:
            lines += ["| Script | Mean CER | Sample Count |", "|---|---|---|"]
            for script, sdata in run.indic_cer_by_script.items():
                s = sdata.get("cer_stats", {})
                mean_val = s.get("mean")
                sc = s.get("sample_count", 0)
                lines.append(f"| {script} | {'N/A' if mean_val is None else f'{mean_val:.4f}'} | {sc} |")
        else:
            lines.append("No Indic script data available.")
        lines.append("")

        # 10. Failure taxonomy summary
        failure_counts: Dict[str, int] = {}
        for doc_res in run.per_document:
            for pr in doc_res.page_results:
                for cat in pr.failure_categories:
                    failure_counts[cat] = failure_counts.get(cat, 0) + 1
        lines += ["## 9. Failure Taxonomy Summary", ""]
        if failure_counts:
            lines += ["| Category | Count |", "|---|---|"]
            for cat, cnt in sorted(failure_counts.items()):
                lines.append(f"| {cat} | {cnt} |")
        else:
            lines.append("No failures recorded.")
        lines.append("")

        # 11. Per-document summary
        lines += [
            "## 10. Per-Document Summary",
            "",
            "| Document ID | Expected Class | Predicted Class | Correct | Evaluated Pages | "
            "Mean CER | Mean WER |",
            "|---|---|---|---|---|---|---|",
        ]
        for dr in run.per_document:
            mean_cer = dr.cer_stats.get("mean")
            mean_wer = dr.wer_stats.get("mean")
            lines.append(
                f"| {dr.document_id} | {dr.expected_document_class} | "
                f"{dr.predicted_document_class} | {dr.document_class_correct} | "
                f"{dr.evaluated_page_count} | "
                f"{'N/A' if mean_cer is None else f'{mean_cer:.4f}'} | "
                f"{'N/A' if mean_wer is None else f'{mean_wer:.4f}'} |"
            )
        lines.append("")

        # 12. Disclaimer block (bottom)
        lines += [
            "---",
            "",
            "> **DISCLAIMER**: " + _DISCLAIMER,
        ]

        return "\n".join(lines)
