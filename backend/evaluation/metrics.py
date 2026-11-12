"""
metrics.py — CER/WER, Classification, and OCR Correlation Metrics (Phase 7).

ALGORITHM: Python difflib.SequenceMatcher Approximate Edit Distance.
This is NOT canonical Wagner-Fischer Levenshtein edit distance.
The algorithm name must appear in all EvaluationRun records.

LEGAL ACCURACY DISCLAIMER:
All metrics in this module measure transcription/representation fidelity only.
They do NOT measure legal accuracy, semantic correctness, contractual correctness,
or legal validity.
"""

from __future__ import annotations

import difflib
import statistics
from typing import Dict, List, Optional, Tuple

from evaluation.normalizer import normalize_for_cer, normalize_for_wer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CER_WER_ALGORITHM: str = "difflib.SequenceMatcher (Python 3.12)"

LEGAL_ACCURACY_DISCLAIMER: str = (
    "All metrics in this evaluation run measure transcription/representation fidelity only. "
    "NOT legal accuracy, semantic correctness, contractual correctness, or legal validity."
)


# ---------------------------------------------------------------------------
# Core edit distance (difflib-based, autojunk=False required)
# ---------------------------------------------------------------------------

def _seq_edit_distance(seq_a: list, seq_b: list) -> int:
    """
    Compute approximate edit distance using difflib.SequenceMatcher.

    Algorithm: Python difflib.SequenceMatcher (Python 3.12)
    autojunk=False is MANDATORY to ensure deterministic results.

    NOT equivalent to Wagner-Fischer Levenshtein in all edge cases due to
    SequenceMatcher's longest-common-subsequence heuristics.
    """
    matcher = difflib.SequenceMatcher(None, seq_a, seq_b, autojunk=False)
    distance = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            distance += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            distance += i2 - i1
        elif tag == "insert":
            distance += j2 - j1
    return distance


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


# ---------------------------------------------------------------------------
# CER / WER with exact edge-case definitions
# ---------------------------------------------------------------------------

def compute_cer(
    reference: str,
    predicted: str,
    preserve_joiners: bool = False,
) -> Tuple[float, int]:
    """
    Compute Character Error Rate using SequenceMatcher Approximate Edit Distance.

    Edge cases (applied after normalization):
      Case 1: ref == "" and pred == ""  → CER = 0.0
      Case 2: ref == "" and pred != ""  → CER = 1.0  (false positive extraction)
      Case 3: ref != "" and pred == ""  → CER = 1.0  (total extraction failure)
      Case 4: whitespace-only → after Step 4 normalization becomes ""; apply Case 1/2/3
      Case 5: [UNCLEAR]-only → retained as literal characters; rules above still apply

    Returns:
        (cer: float in [0.0, 1.0], ref_char_count: int)
        ref_char_count is the denominator (len of normalized reference).
    """
    norm_ref = normalize_for_cer(reference, preserve_joiners)
    norm_pred = normalize_for_cer(predicted, preserve_joiners)

    ref_chars = list(norm_ref)
    pred_chars = list(norm_pred)

    ref_len = len(ref_chars)
    pred_len = len(pred_chars)

    # Case 1
    if ref_len == 0 and pred_len == 0:
        return 0.0, 0

    # Case 2: empty reference, non-empty predicted
    if ref_len == 0 and pred_len > 0:
        return 1.0, 0

    # Case 3: non-empty reference, empty predicted
    if ref_len > 0 and pred_len == 0:
        return 1.0, ref_len

    dist = _seq_edit_distance(ref_chars, pred_chars)
    cer = _clamp(dist / ref_len)
    return cer, ref_len


def compute_wer(
    reference: str,
    predicted: str,
    preserve_joiners: bool = False,
) -> Tuple[float, int]:
    """
    Compute Word Error Rate using SequenceMatcher Approximate Edit Distance.

    Edge cases (applied after normalization):
      Case 1: ref == [] and pred == []  → WER = 0.0
      Case 2: ref == [] and pred != []  → WER = 1.0
      Case 3: ref != [] and pred == []  → WER = 1.0
      Case 4: whitespace-only → normalizes to empty list; apply Case 1/2/3
      Case 5: [UNCLEAR]-only → treated as single word token; rules above still apply

    Returns:
        (wer: float in [0.0, 1.0], ref_word_count: int)
        ref_word_count is the denominator (word count of normalized reference).
    """
    ref_words = normalize_for_wer(reference, preserve_joiners)
    pred_words = normalize_for_wer(predicted, preserve_joiners)

    ref_len = len(ref_words)
    pred_len = len(pred_words)

    # Case 1
    if ref_len == 0 and pred_len == 0:
        return 0.0, 0

    # Case 2: empty reference, non-empty predicted
    if ref_len == 0 and pred_len > 0:
        return 1.0, 0

    # Case 3: non-empty reference, empty predicted
    if ref_len > 0 and pred_len == 0:
        return 1.0, ref_len

    dist = _seq_edit_distance(ref_words, pred_words)
    wer = _clamp(dist / ref_len)
    return wer, ref_len


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------

def aggregate_stats(values: List[float], label: str = "") -> Dict:
    """
    Compute descriptive statistics over a list of floats.

    Always includes sample_count (denominator). Never reports a percentage
    without its population.

    Returns dict with: label, sample_count, mean, median, p95, min, max,
    std_dev, insufficient_data.
    """
    n = len(values)
    if n == 0:
        return {
            "label": label,
            "sample_count": 0,
            "mean": None,
            "median": None,
            "p95": None,
            "min": None,
            "max": None,
            "std_dev": None,
            "insufficient_data": True,
        }
    sorted_vals = sorted(values)
    p95_idx = min(int(0.95 * n), n - 1)
    return {
        "label": label,
        "sample_count": n,
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": sorted_vals[p95_idx],
        "min": sorted_vals[0],
        "max": sorted_vals[-1],
        "std_dev": statistics.stdev(values) if n > 1 else 0.0,
        "insufficient_data": False,
    }


# ---------------------------------------------------------------------------
# Page type classification metrics
# ---------------------------------------------------------------------------

def page_type_metrics(
    predicted: List[str],
    expected: List[str],
    classes: Tuple[str, ...] = ("digital", "scanned", "empty"),
) -> Dict:
    """
    Compute per-class precision, recall, F1, support, TP/FP/FN/TN,
    and a confusion matrix.

    Division-by-zero rule: If support == 0 for a class, precision/recall/F1
    are None (not 0.0). None propagates to macro_f1.

    Returns:
        {
          "per_class": {cls: {precision, recall, f1, support, tp, fp, fn, tn}},
          "macro_f1": float | None,
          "sample_count": int,
          "confusion_matrix": {"labels": [...], "matrix": [[...]]}
        }
    """
    n = len(predicted)
    assert n == len(expected), "predicted and expected must have the same length"

    per_class: Dict[str, Dict] = {}
    for cls in classes:
        tp = sum(1 for p, e in zip(predicted, expected) if p == cls and e == cls)
        fp = sum(1 for p, e in zip(predicted, expected) if p == cls and e != cls)
        fn = sum(1 for p, e in zip(predicted, expected) if p != cls and e == cls)
        tn = sum(1 for p, e in zip(predicted, expected) if p != cls and e != cls)
        support = tp + fn  # total expected positives

        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn) if (tp + fn) > 0 else None

        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = None

        per_class[cls] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    # Macro F1 — None if any class has f1=None
    f1_values = [per_class[cls]["f1"] for cls in classes if per_class[cls]["support"] > 0]
    if f1_values and all(v is not None for v in f1_values):
        macro_f1: Optional[float] = statistics.mean(f1_values)  # type: ignore[arg-type]
    else:
        macro_f1 = None

    # Confusion matrix (row=expected, col=predicted)
    labels = list(classes)
    matrix = []
    for exp_cls in labels:
        row = []
        for pred_cls in labels:
            count = sum(
                1 for p, e in zip(predicted, expected)
                if e == exp_cls and p == pred_cls
            )
            row.append(count)
        matrix.append(row)

    return {
        "per_class": per_class,
        "macro_f1": macro_f1,
        "sample_count": n,
        "confusion_matrix": {"labels": labels, "matrix": matrix},
    }


# ---------------------------------------------------------------------------
# Document class accuracy
# ---------------------------------------------------------------------------

def document_class_accuracy(
    predicted: List[str],
    expected: List[str],
) -> Dict:
    """
    Compute document-class classification accuracy.

    Returns: {"correct": int, "total": int, "accuracy": float | None}
    accuracy is None when total == 0.
    """
    total = len(expected)
    if total == 0:
        return {"correct": 0, "total": 0, "accuracy": None}
    correct = sum(1 for p, e in zip(predicted, expected) if p == e)
    return {"correct": correct, "total": total, "accuracy": correct / total}


# ---------------------------------------------------------------------------
# UNCLEAR precision / recall / F1 — frozen definition
# ---------------------------------------------------------------------------

def unclear_metrics(
    predicted_unclear: List[bool],
    expected_unclear: List[bool],
) -> Dict:
    """
    Compute UNCLEAR detection metrics.

    Definitions:
      TP: predicted=True,  expected=True   (correctly flagged unclear)
      FP: predicted=True,  expected=False  (false unclear flag)
      FN: predicted=False, expected=True   (missed unclear page)
      TN: predicted=False, expected=False  (correctly clear)

      Precision = TP / (TP + FP)      [None if TP + FP == 0]
      Recall    = TP / (TP + FN)      [None if TP + FN == 0]
      F1        = 2*P*R / (P+R)       [None if P or R is None or P+R == 0]
      Support   = TP + FN             (total expected UNCLEAR pages)

    Returns:
        {"tp", "fp", "fn", "tn", "precision", "recall", "f1", "support", "sample_count"}
    """
    assert len(predicted_unclear) == len(expected_unclear)

    tp = sum(1 for p, e in zip(predicted_unclear, expected_unclear) if p and e)
    fp = sum(1 for p, e in zip(predicted_unclear, expected_unclear) if p and not e)
    fn = sum(1 for p, e in zip(predicted_unclear, expected_unclear) if not p and e)
    tn = sum(1 for p, e in zip(predicted_unclear, expected_unclear) if not p and not e)
    support = tp + fn

    precision: Optional[float] = tp / (tp + fp) if (tp + fp) > 0 else None
    recall: Optional[float] = tp / (tp + fn) if (tp + fn) > 0 else None

    if precision is not None and recall is not None and (precision + recall) > 0:
        f1: Optional[float] = 2 * precision * recall / (precision + recall)
    else:
        f1 = None

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": support,
        "sample_count": len(predicted_unclear),
    }


# ---------------------------------------------------------------------------
# OCR confidence correlation
# ---------------------------------------------------------------------------

def ocr_confidence_vs_cer_correlation(
    confidences: List[float],
    cers: List[float],
    min_samples: int = 3,
) -> Dict:
    """
    Compute Pearson correlation between OCR engine confidence and CER.
    Called only for pages where ocr_confidence is not None.

    Insufficient data cases (returns None for correlation):
      - sample_count < min_samples
      - All confidence values are identical (stdev = 0)
      - All CER values are identical (stdev = 0)

    NEVER returns 0.0 for undefined correlation.

    Returns:
        {
          "algorithm": "Pearson (statistics stdlib)",
          "sample_count": int,
          "correlation": float | None,
          "insufficient_data": bool,
          "reason": str | None
        }
    """
    n = len(confidences)
    assert n == len(cers), "confidences and cers must have the same length"

    result_base = {
        "algorithm": "Pearson (statistics stdlib)",
        "sample_count": n,
    }

    if n < min_samples:
        return {**result_base, "correlation": None, "insufficient_data": True,
                "reason": f"Insufficient samples: {n} < {min_samples}"}

    try:
        std_conf = statistics.stdev(confidences)
        std_cer = statistics.stdev(cers)
    except statistics.StatisticsError as exc:
        return {**result_base, "correlation": None, "insufficient_data": True,
                "reason": f"Statistics error: {exc}"}

    if std_conf == 0.0:
        return {**result_base, "correlation": None, "insufficient_data": True,
                "reason": "All OCR confidence values are identical (stdev=0); correlation undefined."}

    if std_cer == 0.0:
        return {**result_base, "correlation": None, "insufficient_data": True,
                "reason": "All CER values are identical (stdev=0); correlation undefined."}

    mean_conf = statistics.mean(confidences)
    mean_cer = statistics.mean(cers)

    numerator = sum(
        (c - mean_conf) * (e - mean_cer)
        for c, e in zip(confidences, cers)
    )
    denominator = (n - 1) * std_conf * std_cer
    correlation = numerator / denominator if denominator != 0.0 else None

    if correlation is None:
        return {**result_base, "correlation": None, "insufficient_data": True,
                "reason": "Denominator was zero during correlation computation."}

    # Clamp to [-1, 1] for floating-point safety
    correlation = max(-1.0, min(1.0, correlation))

    return {**result_base, "correlation": correlation, "insufficient_data": False, "reason": None}
