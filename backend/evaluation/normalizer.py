"""
normalizer.py — Versioned Text Normalization Pipeline (Phase 7).

Implements a deterministic, versioned normalization pipeline for computing
CER and WER against human-verified ground-truth references.

Normalization version: 7.1.0

LEGAL ACCURACY DISCLAIMER:
These normalization functions operate on extracted text for transcription
fidelity comparison only. They do NOT measure legal accuracy, semantic
correctness, contractual correctness, or legal validity.
"""

from __future__ import annotations

import re
import string
import unicodedata
from typing import List

# ---------------------------------------------------------------------------
# Version constant — bump when any normalization rule changes
# ---------------------------------------------------------------------------

NORMALIZER_VERSION: str = "7.1.0"

# ---------------------------------------------------------------------------
# Punctuation set for WER (Step 5, applied ONLY for WER, not CER)
# ---------------------------------------------------------------------------
# Standard ASCII punctuation plus common Unicode equivalents.
_WER_PUNCT_BASE: frozenset = frozenset(string.punctuation) | frozenset({
    "\u2013",  # en dash
    "\u2014",  # em dash
    "\u2018",  # left single quote
    "\u2019",  # right single quote
    "\u201C",  # left double quote
    "\u201D",  # right double quote
    "\u00AB",  # left-pointing double angle quotation mark
    "\u00BB",  # right-pointing double angle quotation mark
})
# Square brackets excluded so [UNCLEAR] tokens survive WER tokenization as a
# single word token per spec Section 6 Step 6.
_WER_PUNCT: frozenset = _WER_PUNCT_BASE - frozenset({"[", "]"})


def _step1_nfkc(text: str) -> str:
    """
    Step 1 — NFKC Unicode Normalization.

    Effect: Converts compatibility variants to canonical forms.
    - Half-width katakana → full-width.
    - Superscript/subscript digits → plain digits.
    - Ligatures (ﬁ, ﬂ) → 'fi', 'fl'.

    What is preserved: All standard characters, Indic base characters,
    punctuation, digits.
    What changes: Only Unicode compatibility equivalents.
    No semantic content is removed.
    """
    return unicodedata.normalize("NFKC", text)


def _step2_nfc_nukta(text: str) -> str:
    """
    Step 2 — Devanagari Nukta Composition (NFC).

    Effect: Applied after NFKC. Ensures Devanagari sequences with combining
    Nukta (U+093C) are composed into precomposed forms where available.
    Example: 'क' (U+0915) + '़' (U+093C) → precomposed form.

    What is preserved: All Indic text. Nukta is never silently discarded;
    it is either composed or retained as a combining character.
    """
    return unicodedata.normalize("NFC", text)


def _step3_strip_joiners(text: str, preserve_joiners: bool) -> str:
    """
    Step 3 — ZWJ / ZWNJ Handling.

    Default (preserve_joiners=False): Removes Zero-Width Joiner (U+200D)
    and Zero-Width Non-Joiner (U+200C).

    Rationale: In plain-text CER/WER, these control characters do not affect
    rendered output and would unfairly penalize engines that differ in retention.

    What is NOT silently removed: No other zero-width characters beyond
    U+200C and U+200D are removed by this step.

    preserve_joiners=True: Retains ZWJ and ZWNJ unchanged.
    """
    if preserve_joiners:
        return text
    return text.replace("\u200D", "").replace("\u200C", "")


def _step4_whitespace(text: str) -> str:
    """
    Step 4 — Whitespace Normalization.

    Effect: Collapses all runs of whitespace characters to a single ASCII
    space, then strips leading/trailing whitespace.

    Characters collapsed: space, tab (\\t), carriage return (\\r),
    newline (\\n), non-breaking space (U+00A0), ideographic space (U+3000).

    What is preserved: All alphabetic, digit, punctuation, and Indic characters.
    What changes: Multi-space runs, mixed newline sequences.
    """
    return re.sub(r"[ \t\r\n\xa0\u3000]+", " ", text).strip()


def _step5_strip_punct_for_wer(text: str) -> str:
    """
    Step 5 — Punctuation Stripping (WER ONLY, NOT applied for CER).

    Effect: Replaces punctuation characters with a space (not deletion)
    so adjacent word tokens are correctly separated.

    What is NOT stripped: Indic script vowel signs, combining marks,
    digits, alphabetic characters.
    """
    chars = []
    for ch in text:
        if ch in _WER_PUNCT:
            chars.append(" ")
        else:
            chars.append(ch)
    normalized = "".join(chars)
    return re.sub(r" +", " ", normalized).strip()


# ---------------------------------------------------------------------------
# Step 6 — [UNCLEAR] token handling
# ---------------------------------------------------------------------------
# [UNCLEAR] tokens are RETAINED as literal text through all normalization steps.
# They are not stripped, not replaced, not counted as errors by convention.
# - For CER: treated as a 9-character sequence (including brackets).
# - For WER: treated as a single word token after split().
# No additional action required; the steps above naturally preserve [UNCLEAR].


# ---------------------------------------------------------------------------
# Public normalization API
# ---------------------------------------------------------------------------

def normalize_for_cer(
    text: str,
    preserve_joiners: bool = False,
) -> str:
    """
    Apply normalization Steps 1–4 and Step 6 (implicit).

    Returns a character sequence suitable for CER computation.
    Punctuation is NOT stripped (Step 5 not applied).

    [UNCLEAR] tokens are preserved as literal characters.

    Args:
        text: Raw input text (reference or predicted).
        preserve_joiners: If True, ZWJ/ZWNJ are retained (Step 3 skipped).

    Returns:
        Normalized string for character-level comparison.
    """
    text = _step1_nfkc(text)
    text = _step2_nfc_nukta(text)
    text = _step3_strip_joiners(text, preserve_joiners)
    text = _step4_whitespace(text)
    return text


def normalize_for_wer(
    text: str,
    preserve_joiners: bool = False,
) -> List[str]:
    """
    Apply normalization Steps 1–6.

    Returns a word token list suitable for WER computation.
    Punctuation IS stripped (Step 5 applied before tokenization).

    [UNCLEAR] tokens are preserved as single word tokens.

    Args:
        text: Raw input text (reference or predicted).
        preserve_joiners: If True, ZWJ/ZWNJ are retained (Step 3 skipped).

    Returns:
        List of word strings for word-level comparison.
    """
    text = _step1_nfkc(text)
    text = _step2_nfc_nukta(text)
    text = _step3_strip_joiners(text, preserve_joiners)
    text = _step4_whitespace(text)
    text = _step5_strip_punct_for_wer(text)
    if not text:
        return []
    return text.split()
