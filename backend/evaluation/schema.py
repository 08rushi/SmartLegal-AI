"""
schema.py — Ground-Truth Data Model & Serialization (Phase 7).

Defines all dataclasses for ground-truth annotation, evaluation results,
and the EvaluationRun aggregate.

LEGAL ACCURACY DISCLAIMER:
All metrics in this module measure transcription/representation fidelity only.
They do NOT measure legal accuracy, semantic correctness, contractual correctness,
or legal validity.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Dict, List, Optional


# ---------------------------------------------------------------------------
# Versioning constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION: str = "7.1"


# ---------------------------------------------------------------------------
# Failure categories
# ---------------------------------------------------------------------------

class FailureCategory:
    EXTRACTION_EMPTY      = "extraction_empty"
    OCR_LOW_CONFIDENCE    = "ocr_low_confidence"
    OCR_UNCLEAR_FLAG      = "ocr_unclear_flag"
    CLASSIFICATION_MISMATCH = "classification_mismatch"
    HIGH_CER              = "high_cer"
    HIGH_WER              = "high_wer"
    ANNOTATION_INCOMPLETE = "annotation_incomplete"
    PROVIDER_ERROR        = "provider_error"
    HASH_MISMATCH         = "hash_mismatch"


# ---------------------------------------------------------------------------
# Ground-Truth Input Types
# ---------------------------------------------------------------------------

@dataclass
class AnnotatorMetadata:
    """Provenance and review lifecycle for a single page annotation."""
    annotator_id: str
    annotation_date: str
    review_state: str               # "draft" | "review_pending" | "approved" | "rejected"
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotator_id": self.annotator_id,
            "annotation_date": self.annotation_date,
            "review_state": self.review_state,
            "reviewer_id": self.reviewer_id,
            "reviewed_at": self.reviewed_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnnotatorMetadata":
        return cls(
            annotator_id=d.get("annotator_id", "unknown"),
            annotation_date=d.get("annotation_date", ""),
            review_state=d.get("review_state", "draft"),
            reviewer_id=d.get("reviewer_id"),
            reviewed_at=d.get("reviewed_at"),
            notes=d.get("notes", ""),
        )


@dataclass
class GroundTruthPage:
    """Human-verified annotation for a single document page."""
    page_num: int
    reference_text: str
    script: str
    expected_page_type: str         # "digital" | "scanned" | "empty"
    expected_is_unclear: bool
    annotation: AnnotatorMetadata
    annotation_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_num": self.page_num,
            "reference_text": self.reference_text,
            "script": self.script,
            "expected_page_type": self.expected_page_type,
            "expected_is_unclear": self.expected_is_unclear,
            "annotation": self.annotation.to_dict(),
            "annotation_version": self.annotation_version,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GroundTruthPage":
        return cls(
            page_num=d["page_num"],
            reference_text=d["reference_text"],
            script=d.get("script", "Latin / English"),
            expected_page_type=d.get("expected_page_type", "digital"),
            expected_is_unclear=d.get("expected_is_unclear", False),
            annotation=AnnotatorMetadata.from_dict(d.get("annotation", {
                "annotator_id": "unknown",
                "annotation_date": "",
                "review_state": "draft",
            })),
            annotation_version=d.get("annotation_version", "1.0"),
        )


@dataclass
class GroundTruthDocument:
    """Full ground-truth annotation for a document."""
    corpus_id: str
    corpus_version: str
    document_id: str
    filename: str
    source_hash: str                # SHA-256 hex digest of original PDF bytes
    document_type: str
    expected_document_class: str    # "digital_pdf" | "scanned_pdf" | "mixed_pdf" | "empty_pdf"
    language: str
    indic_scripts: List[str]
    page_count: int
    pages: List[GroundTruthPage]
    dataset_version: str
    schema_version: str
    created_at: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "document_id": self.document_id,
            "filename": self.filename,
            "source_hash": self.source_hash,
            "document_type": self.document_type,
            "expected_document_class": self.expected_document_class,
            "language": self.language,
            "indic_scripts": self.indic_scripts,
            "page_count": self.page_count,
            "pages": [p.to_dict() for p in self.pages],
            "dataset_version": self.dataset_version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GroundTruthDocument":
        return cls(
            corpus_id=d["corpus_id"],
            corpus_version=d["corpus_version"],
            document_id=d["document_id"],
            filename=d["filename"],
            source_hash=d["source_hash"],
            document_type=d.get("document_type", "unknown"),
            expected_document_class=d["expected_document_class"],
            language=d.get("language", "en"),
            indic_scripts=d.get("indic_scripts", []),
            page_count=d["page_count"],
            pages=[GroundTruthPage.from_dict(p) for p in d.get("pages", [])],
            dataset_version=d["dataset_version"],
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            created_at=d.get("created_at", ""),
            notes=d.get("notes", ""),
        )

    @classmethod
    def load_from_file(cls, path: str) -> "GroundTruthDocument":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    def save_to_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, ensure_ascii=False, indent=2)


def compute_source_hash(pdf_bytes: bytes) -> str:
    """Compute SHA-256 hex digest of raw PDF bytes."""
    return hashlib.sha256(pdf_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Evaluation Result Types
# ---------------------------------------------------------------------------

_DISCLAIMER = (
    "CER/WER measures transcription fidelity only. "
    "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
)

_AGG_DISCLAIMER = (
    "All metrics measure transcription/representation fidelity only. "
    "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
)


@dataclass
class PageEvaluationResult:
    """Evaluation result for a single document page."""
    page_num: int
    review_state: str               # "approved" | "skipped" | "failed" | "unavailable"
    extraction_source: str

    cer: Optional[float]
    wer: Optional[float]
    cer_ref_char_count: int
    wer_ref_word_count: int

    predicted_page_type: Optional[str]
    expected_page_type: str
    page_type_correct: Optional[bool]

    predicted_is_unclear: Optional[bool]
    expected_is_unclear: bool
    unclear_match: Optional[str]    # "TP" | "FP" | "FN" | "TN" | None

    ocr_confidence: Optional[float]
    quality_score: Optional[float]

    failure_categories: List[str]

    reference_text_raw: str
    predicted_text_raw: str

    DISCLAIMER: ClassVar[str] = _DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_num": self.page_num,
            "review_state": self.review_state,
            "extraction_source": self.extraction_source,
            "cer": self.cer,
            "wer": self.wer,
            "cer_ref_char_count": self.cer_ref_char_count,
            "wer_ref_word_count": self.wer_ref_word_count,
            "predicted_page_type": self.predicted_page_type,
            "expected_page_type": self.expected_page_type,
            "page_type_correct": self.page_type_correct,
            "predicted_is_unclear": self.predicted_is_unclear,
            "expected_is_unclear": self.expected_is_unclear,
            "unclear_match": self.unclear_match,
            "ocr_confidence": self.ocr_confidence,
            "quality_score": self.quality_score,
            "failure_categories": self.failure_categories,
            "DISCLAIMER": self.DISCLAIMER,
        }


@dataclass
class DocumentEvaluationResult:
    """Evaluation result for a complete document."""
    doc_id: str
    corpus_id: str
    document_id: str
    filename: str
    source_hash: str

    predicted_document_class: str
    expected_document_class: str
    document_class_correct: bool

    total_pages_in_document: int
    evaluated_page_count: int
    skipped_page_count: int
    failed_page_count: int
    unavailable_page_count: int

    cer_stats: Dict[str, Any]
    wer_stats: Dict[str, Any]

    page_type_metrics: Dict[str, Any]
    unclear_metrics: Dict[str, Any]
    ocr_correlation: Dict[str, Any]

    page_results: List[PageEvaluationResult]

    DISCLAIMER: ClassVar[str] = _AGG_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "corpus_id": self.corpus_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "source_hash": self.source_hash,
            "predicted_document_class": self.predicted_document_class,
            "expected_document_class": self.expected_document_class,
            "document_class_correct": self.document_class_correct,
            "counts": {
                "total_pages_in_document": self.total_pages_in_document,
                "evaluated_page_count": self.evaluated_page_count,
                "skipped_page_count": self.skipped_page_count,
                "failed_page_count": self.failed_page_count,
                "unavailable_page_count": self.unavailable_page_count,
            },
            "cer_stats": self.cer_stats,
            "wer_stats": self.wer_stats,
            "page_type_metrics": self.page_type_metrics,
            "unclear_metrics": self.unclear_metrics,
            "ocr_correlation": self.ocr_correlation,
            "page_results": [p.to_dict() for p in self.page_results],
            "DISCLAIMER": self.DISCLAIMER,
        }


@dataclass
class Phase6ComparisonResult:
    """Paired before/after Phase 6 optimization comparison for a document."""
    doc_id: str
    corpus_id: str
    document_id: str
    source_hash: str
    filename: str

    optimization_applied: bool
    optimization_method: str
    original_size_bytes: int
    optimized_size_bytes: int
    compression_ratio: float

    baseline_cer_stats: Dict[str, Any]
    post_cer_stats: Dict[str, Any]
    cer_delta_mean: float

    baseline_wer_stats: Dict[str, Any]
    post_wer_stats: Dict[str, Any]
    wer_delta_mean: float

    paired_page_count: int
    improved_page_count: int
    unchanged_page_count: int
    degraded_page_count: int
    skipped_page_count: int
    failed_page_count: int

    telemetry: Dict[str, Any]

    DISCLAIMER: ClassVar[str] = (
        "CER/WER deltas measure transcription fidelity change due to optimization. "
        "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "corpus_id": self.corpus_id,
            "document_id": self.document_id,
            "source_hash": self.source_hash,
            "filename": self.filename,
            "optimization_applied": self.optimization_applied,
            "optimization_method": self.optimization_method,
            "original_size_bytes": self.original_size_bytes,
            "optimized_size_bytes": self.optimized_size_bytes,
            "compression_ratio": self.compression_ratio,
            "baseline_cer_stats": self.baseline_cer_stats,
            "post_cer_stats": self.post_cer_stats,
            "cer_delta_mean": self.cer_delta_mean,
            "baseline_wer_stats": self.baseline_wer_stats,
            "post_wer_stats": self.post_wer_stats,
            "wer_delta_mean": self.wer_delta_mean,
            "page_counts": {
                "paired": self.paired_page_count,
                "improved": self.improved_page_count,
                "unchanged": self.unchanged_page_count,
                "degraded": self.degraded_page_count,
                "skipped": self.skipped_page_count,
                "failed": self.failed_page_count,
            },
            "telemetry": self.telemetry,
            "DISCLAIMER": self.DISCLAIMER,
        }


@dataclass
class EvaluationRun:
    """Top-level aggregate result for a complete evaluation run."""
    run_id: str
    timestamp: str
    git_commit: str
    schema_version: str
    normalizer_version: str
    cer_wer_algorithm: str
    normalization_config: Dict[str, Any]

    corpus_id: str
    corpus_version: str
    dataset_version: str

    total_documents: int
    evaluated_document_count: int
    total_pages_across_documents: int
    evaluated_page_count: int
    skipped_page_count: int
    failed_page_count: int
    unavailable_page_count: int

    cer_stats: Dict[str, Any]
    wer_stats: Dict[str, Any]
    document_class_accuracy: Dict[str, Any]
    page_type_metrics: Dict[str, Any]
    unclear_metrics: Dict[str, Any]
    indic_cer_by_script: Dict[str, Any]

    per_document: List[DocumentEvaluationResult]

    DISCLAIMER: ClassVar[str] = (
        "All metrics in this evaluation run measure transcription/representation fidelity only. "
        "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "schema_version": self.schema_version,
            "normalizer_version": self.normalizer_version,
            "cer_wer_algorithm": self.cer_wer_algorithm,
            "normalization_config": self.normalization_config,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "dataset_version": self.dataset_version,
            "counts": {
                "total_documents": self.total_documents,
                "evaluated_documents": self.evaluated_document_count,
                "total_pages": self.total_pages_across_documents,
                "evaluated_pages": self.evaluated_page_count,
                "skipped_pages": self.skipped_page_count,
                "failed_pages": self.failed_page_count,
                "unavailable_pages": self.unavailable_page_count,
            },
            "cer_stats": self.cer_stats,
            "wer_stats": self.wer_stats,
            "document_class_accuracy": self.document_class_accuracy,
            "page_type_metrics": self.page_type_metrics,
            "unclear_metrics": self.unclear_metrics,
            "indic_cer_by_script": self.indic_cer_by_script,
            "per_document": [d.to_dict() for d in self.per_document],
            "DISCLAIMER": self.DISCLAIMER,
        }
