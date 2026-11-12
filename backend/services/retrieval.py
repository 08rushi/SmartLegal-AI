"""
retrieval.py — pick the parts of a long document that are relevant to a question.

Chat prompts can only carry ~12K characters. Sending just the first 12K made it impossible to
ask about later pages of a long contract. This does cheap, local, free relevance selection
(keyword overlap, Unicode-aware so Hindi/Marathi etc. work) — no embeddings, no API cost.
"""

from __future__ import annotations

import math
import re
from typing import List, Tuple

_PAGE_RE = re.compile(r"(?m)^\[Page (\d+)\]\s*$")
# \w alone drops Indic vowel signs (matras), splitting Hindi/Marathi words into fragments,
# so also accept the whole Devanagari → Malayalam block range (U+0900–U+0D7F).
_WORD_RE = re.compile(r"[\wऀ-ൿ]{3,}", re.UNICODE)
_STOP = {
    "the", "and", "for", "that", "this", "with", "what", "which", "who", "whom", "when", "where", "how", "why",
    "are", "was", "were", "can", "does", "did", "will", "shall", "have", "has", "had", "from", "into", "about",
    "any", "all", "you", "your", "not", "but", "than", "then", "there", "their", "them", "tell", "explain",
    "please", "document", "clause", "agreement",
}
_SECTION_CHARS = 2400   # window size when the text has no [Page N] markers


def _split_sections(text: str) -> List[Tuple[str, str]]:
    """[(label, body)] — one per page when markers exist, else ~2.4K-character windows."""
    parts = _PAGE_RE.split(text)
    if len(parts) > 1:
        sections: List[Tuple[str, str]] = []
        if parts[0].strip():
            sections.append(("", parts[0].strip()))
        for i in range(1, len(parts) - 1, 2):
            body = parts[i + 1].strip()
            if body:
                sections.append((f"[Page {parts[i]}]", body))
        return sections or [("", text)]

    sections = []
    buf = ""
    for para in re.split(r"\n\s*\n", text):
        if buf and len(buf) + len(para) > _SECTION_CHARS:
            sections.append(("", buf.strip()))
            buf = ""
        buf += para + "\n\n"
    if buf.strip():
        sections.append(("", buf.strip()))
    return sections or [("", text)]


def _fmt(label: str, body: str) -> str:
    return f"{label}\n{body}" if label else body


def select_relevant_text(doc_text: str, question: str, max_chars: int = 12000) -> str:
    """
    Return at most ~max_chars of the document: always the opening (title/parties), then the
    sections that best match the question, then — if room is left — the following sections in
    order. Short documents are returned unchanged.
    """
    if not doc_text or len(doc_text) <= max_chars:
        return doc_text

    sections = _split_sections(doc_text)
    q_terms = {w.lower() for w in _WORD_RE.findall(question or "")} - _STOP

    scored: List[Tuple[float, int]] = []
    for i, (_label, body) in enumerate(sections):
        if i == 0:
            continue  # opening is always included
        words = [w.lower() for w in _WORD_RE.findall(body)]
        if not words or not q_terms:
            continue
        distinct = len(q_terms & set(words))
        if distinct == 0:
            continue
        hits = sum(1 for w in words if w in q_terms)
        scored.append((distinct * 3 + hits / math.sqrt(len(words)), i))

    chosen = {0}
    used = len(_fmt(*sections[0]))

    def _try_add(i: int) -> None:
        nonlocal used
        size = len(_fmt(*sections[i])) + 4
        if i not in chosen and used + size <= max_chars:
            chosen.add(i)
            used += size

    for _score, i in sorted(scored, reverse=True):
        _try_add(i)
    for i in range(1, len(sections)):     # fill remaining room in document order
        _try_add(i)

    ordered = sorted(chosen)
    out: List[str] = []
    prev = None
    for i in ordered:
        if prev is not None and i != prev + 1:
            out.append("[… part of the document omitted …]")
        out.append(_fmt(*sections[i]))
        prev = i
    result = "\n\n".join(out)
    return result[: max_chars + 200]
