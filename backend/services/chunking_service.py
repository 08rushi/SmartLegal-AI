"""
chunking_service.py — Token-Aware Chunking & Partial-Failure Handling (Phase 3).

Key Capabilities:
  1. Token Estimation: Conservative script-aware estimator.
     - Indic scripts (Devanagari, Tamil, Telugu, etc.): ~2.5 characters / token.
     - Latin / English / other scripts: ~3.5 characters / token.
     - Distinguishes estimated_tokens from actual_tokens_used.
  2. Safe Sizing: Configurable max chunk tokens and safety margin derived from ModelCapability.
     - Guaranteed bounded chunk size (overrun capped at <= 10%).
  3. Page Boundaries: Coalesces whole pages into chunks whenever they fit within budget.
  4. Oversized Page Splitting: Deterministic hierarchical splitting:
     paragraphs (\\n\\n) -> sentences (. / । / \\n) -> lines (\\n) -> character window.
  5. Document Ordering: Strictly preserves page order and intra-page text flow.
  6. Partial-Failure & Bounded Retry:
     - Error classification: transient, rate_limit, permanent, malformed_response.
     - Preserves successful chunks when another chunk fails.
     - Computes deterministic completion_ratio and tracks incomplete_chunks.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Union

from config import get_settings
from services.model_capabilities import ModelCapability, get_capability
from services.page_content import PageContent

logger = logging.getLogger(__name__)

# =============================================================================
# Constants & Defaults
# =============================================================================

# Conservative token estimation rates
INDIC_CHARS_PER_TOKEN = 2.5
LATIN_CHARS_PER_TOKEN = 3.5

# Default token budget thresholds
DEFAULT_MAX_CHUNK_TOKENS = 2500
DEFAULT_SAFETY_MARGIN_TOKENS = 1500
MAX_CHUNK_TOLERANCE_RATIO = 1.10  # Maximum allowable estimation overrun (~10%)

# Unicode ranges for Indic scripts (matching pdf_parser._INDIC_RANGES)
_INDIC_RANGES = [
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x0A00, 0x0A7F, "Gurmukhi"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B00, 0x0B7F, "Odia"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0600, 0x06FF, "Urdu / Arabic"),
]


# =============================================================================
# Token Estimation
# =============================================================================

def is_indic_char(ch: str) -> bool:
    """Check if a character falls within any recognized Indic Unicode block."""
    code = ord(ch)
    return any(lo <= code <= hi for lo, hi, _ in _INDIC_RANGES)


def estimate_tokens(text: str) -> int:
    """
    Conservative, deterministic token estimator.

    Accounts for the token-density of Indic scripts where sub-word tokenizers
    produce significantly more tokens per character than in English.
    - Indic characters: ~2.5 chars / token.
    - Latin / English / numbers / symbols: ~3.5 chars / token.

    Note: This is an estimation metric (estimated_tokens), not actual provider token usage.
    """
    if not text:
        return 0

    indic_count = sum(1 for ch in text if is_indic_char(ch))
    other_count = len(text) - indic_count

    estimated = (indic_count / INDIC_CHARS_PER_TOKEN) + (other_count / LATIN_CHARS_PER_TOKEN)
    return max(1, int(math.ceil(estimated)))


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class DocumentChunk:
    """
    Represents a discrete token-bounded text slice ready for LLM reasoning.
    """
    chunk_id: str
    """Unique identifier for this chunk (e.g. 'chunk_1', 'chunk_2_part_1')."""

    chunk_index: int
    """0-indexed sequential position in the document."""

    page_start: int
    """1-indexed starting page number."""

    page_end: int
    """1-indexed ending page number."""

    page_numbers: List[int]
    """List of all page numbers represented in this chunk."""

    text: str
    """Extracted text content with page boundaries preserved."""

    estimated_tokens: int
    """Estimated token count calculated by estimate_tokens()."""

    is_split_page: bool = False
    """True if this chunk is a fragment of an oversized single page."""

    sub_chunk_index: Optional[int] = None
    """Sub-chunk index if split from an oversized page."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to standard dictionary format."""
        return {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "start_page": self.page_start,
            "end_page": self.page_end,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "page_numbers": self.page_numbers,
            "text": self.text,
            "estimated_tokens": self.estimated_tokens,
            "is_split_page": self.is_split_page,
            "sub_chunk_index": self.sub_chunk_index,
        }


@dataclass
class ChunkExecutionResult:
    """
    Result of processing an individual DocumentChunk through an AI provider.
    """
    chunk_id: str
    chunk_index: int
    page_start: int
    page_end: int
    success: bool
    clauses: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # 'transient', 'rate_limit', 'permanent', 'malformed_response'
    retries_attempted: int = 0
    actual_tokens_used: Optional[int] = None


# =============================================================================
# Safe Budget Calculation
# =============================================================================

def get_safe_chunk_budget(
    capability: Optional[ModelCapability] = None,
    max_chunk_tokens: Optional[int] = None,
    safety_margin: Optional[int] = None,
) -> int:
    """
    Calculate the safe maximum token budget for chunk content.

    Reserves space for:
      - system prompt
      - user prompt instructions & Indian Acts context
      - structured output schema overhead
      - model response tokens

    Uses ModelCapability.context_window and max_output_tokens if available.
    """
    margin = safety_margin if safety_margin is not None else DEFAULT_SAFETY_MARGIN_TOKENS
    target_max = max_chunk_tokens if max_chunk_tokens is not None else DEFAULT_MAX_CHUNK_TOKENS

    if capability is not None:
        # Context window available from Phase 1 registry
        available_context = capability.context_window - capability.max_output_tokens - margin
        safe_budget = max(500, min(target_max, available_context))
    else:
        safe_budget = target_max

    return safe_budget


# =============================================================================
# Chunking Service
# =============================================================================

class ChunkingService:
    """
    Dedicated Token-Aware Chunking Service.

    Consumes PageContent lists (or plain text) and produces DocumentChunk objects
    that strictly adhere to token budgets, safety margins, and page ordering.
    """

    def __init__(
        self,
        max_chunk_tokens: int = DEFAULT_MAX_CHUNK_TOKENS,
        safety_margin: int = DEFAULT_SAFETY_MARGIN_TOKENS,
        capability: Optional[ModelCapability] = None,
    ):
        self.safety_margin = safety_margin
        self.capability = capability
        self.safe_budget = get_safe_chunk_budget(capability, max_chunk_tokens, safety_margin)
        self.max_allowed_tokens = int(self.safe_budget * MAX_CHUNK_TOLERANCE_RATIO)

    def chunk_pages(self, pages: List[PageContent]) -> List[DocumentChunk]:
        """
        Produce token-bounded DocumentChunks from a list of PageContent instances.

        Rules:
          1. Whole pages are coalesced sequentially as long as chunk tokens <= safe_budget.
          2. When adding the next page would exceed safe_budget:
             - If current chunk is non-empty: finalize current chunk, start a new one.
             - If current chunk is empty and page exceeds safe_budget: split that oversized page.
          3. Document page order is strictly preserved.
        """
        chunks: List[DocumentChunk] = []
        if not pages:
            return chunks

        current_pages: List[PageContent] = []
        current_text_parts: List[str] = []
        current_tokens: int = 0
        chunk_counter: int = 0

        def _flush_current_chunk():
            nonlocal chunk_counter, current_pages, current_text_parts, current_tokens
            if not current_pages:
                return

            full_chunk_text = "\n\n".join(current_text_parts).strip()
            est_tokens = estimate_tokens(full_chunk_text)
            p_start = current_pages[0].page_num
            p_end = current_pages[-1].page_num
            p_nums = [p.page_num for p in current_pages]

            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{chunk_counter + 1}",
                    chunk_index=chunk_counter,
                    page_start=p_start,
                    page_end=p_end,
                    page_numbers=p_nums,
                    text=full_chunk_text,
                    estimated_tokens=est_tokens,
                    is_split_page=False,
                )
            )
            chunk_counter += 1
            current_pages = []
            current_text_parts = []
            current_tokens = 0

        for page in pages:
            page_body = page.text.strip()
            if not page_body:
                # Still track empty pages if preceding chunk is open
                continue

            page_repr = f"[Page {page.page_num}]\n{page_body}"
            page_tokens = estimate_tokens(page_repr)

            # Check if this single page by itself exceeds the safe budget
            if page_tokens > self.max_allowed_tokens:
                # Flush whatever was pending
                _flush_current_chunk()

                # Split oversized page deterministically
                split_chunks = self._split_oversized_page(page, chunk_counter)
                chunks.extend(split_chunks)
                chunk_counter += len(split_chunks)
                continue

            # Check if adding this page would exceed the budget
            if current_pages and (current_tokens + page_tokens > self.safe_budget):
                _flush_current_chunk()

            current_pages.append(page)
            current_text_parts.append(page_repr)
            current_tokens += page_tokens

        _flush_current_chunk()
        return chunks

    def chunk_text(self, text: str) -> List[DocumentChunk]:
        """
        Backward-compatible entry point for plain strings.
        Parses [Page N] boundary markers if present; otherwise treats text as a single page.
        """
        if not text or not text.strip():
            return []

        # Parse text into synthetic PageContent objects by [Page N] markers
        pages: List[PageContent] = []
        page_pattern = re.compile(r"\[Page (\d+)\]\s*", re.IGNORECASE)
        splits = page_pattern.split(text)

        if len(splits) > 1:
            # First element is text before the first [Page N] marker (usually empty)
            for idx in range(1, len(splits), 2):
                p_num = int(splits[idx])
                p_text = splits[idx + 1].strip()
                if p_text:
                    pages.append(
                        PageContent(
                            page_num=p_num,
                            text=p_text,
                            extraction_source="pymupdf",
                            script="Latin / English",
                        )
                    )
        else:
            pages.append(
                PageContent(
                    page_num=1,
                    text=text.strip(),
                    extraction_source="pymupdf",
                    script="Latin / English",
                )
            )

        return self.chunk_pages(pages)

    def _split_oversized_page(
        self,
        page: PageContent,
        start_chunk_counter: int,
    ) -> List[DocumentChunk]:
        """
        Deterministically split a single page that exceeds the token budget.

        Hierarchical strategy:
          1. Paragraph boundaries (\\n\\n)
          2. Sentence boundaries (. / । / \\n)
          3. Line boundaries (\\n)
          4. Controlled character window fallback
        """
        text = page.text.strip()
        page_num = page.page_num
        header = f"[Page {page_num}]"

        # Split into initial paragraph segments
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        sub_chunks: List[DocumentChunk] = []
        current_paragraphs: List[str] = []
        current_tokens = 0
        sub_idx = 1

        def _flush_sub_chunk():
            nonlocal sub_idx, current_paragraphs, current_tokens, start_chunk_counter
            if not current_paragraphs:
                return

            joined = "\n\n".join(current_paragraphs)
            chunk_text = f"{header}\n{joined}"
            est = estimate_tokens(chunk_text)
            c_idx = start_chunk_counter + len(sub_chunks)

            sub_chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{c_idx + 1}_part_{sub_idx}",
                    chunk_index=c_idx,
                    page_start=page_num,
                    page_end=page_num,
                    page_numbers=[page_num],
                    text=chunk_text,
                    estimated_tokens=est,
                    is_split_page=True,
                    sub_chunk_index=sub_idx,
                )
            )
            sub_idx += 1
            current_paragraphs = []
            current_tokens = 0

        for para in paragraphs:
            para_tokens = estimate_tokens(para)

            # If a single paragraph is itself oversized, split it by sentences/lines
            if para_tokens > self.max_allowed_tokens:
                _flush_sub_chunk()
                sentence_splits = self._split_text_by_sentences(para)
                for sent in sentence_splits:
                    sent_tokens = estimate_tokens(sent)
                    if current_paragraphs and (current_tokens + sent_tokens > self.safe_budget):
                        _flush_sub_chunk()
                    current_paragraphs.append(sent)
                    current_tokens += sent_tokens
                continue

            if current_paragraphs and (current_tokens + para_tokens > self.safe_budget):
                _flush_sub_chunk()

            current_paragraphs.append(para)
            current_tokens += para_tokens

        _flush_sub_chunk()
        return sub_chunks

    def _split_text_by_sentences(self, text: str) -> List[str]:
        """Split text by legal sentence punctuation (. / । / newline / semicolon)."""
        # Split on period, Hindi danda (।), semicolon, or newline followed by space or end
        raw_sentences = re.split(r"(?<=[.।;\n])\s+", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            sentences = [text]

        # If any single sentence is still larger than safe_budget, hard-split by line or chars
        refined: List[str] = []
        for s in sentences:
            if estimate_tokens(s) > self.safe_budget:
                lines = [l.strip() for l in s.split("\n") if l.strip()]
                if len(lines) > 1:
                    refined.extend(lines)
                else:
                    # Fallback character window
                    char_chunk_size = int(self.safe_budget * LATIN_CHARS_PER_TOKEN)
                    for start in range(0, len(s), char_chunk_size):
                        refined.append(s[start:start + char_chunk_size])
            else:
                refined.append(s)

        return refined


# =============================================================================
# Error Classification & Retry Policy
# =============================================================================

def classify_chunk_error(exc: Exception) -> str:
    """
    Deterministically categorize exceptions for retry policy:
      - 'rate_limit': 429, TPM, RPM, quota exceeded
      - 'transient': Connection timeout, 502, 503, 504, network drops
      - 'malformed_response': JSON parse errors, truncated payloads
      - 'permanent': 400 Bad Request, 401 Unauthorized, 403 Forbidden, ValueError
    """
    msg = str(exc).lower()
    if (
        "429" in msg
        or "rate_limit" in msg
        or "rate-limit" in msg
        or "rate limit" in msg
        or "cooloff" in msg
        or "cooldown" in msg
        or "quota" in msg
        or "tpm" in msg
        or "rpm" in msg
        or "too many requests" in msg
    ):
        return "rate_limit"

    if (
        "timeout" in msg
        or "timed out" in msg
        or "502" in msg
        or "503" in msg
        or "504" in msg
        or "connection" in msg
        or "network" in msg
    ):
        return "transient"

    if (
        "json" in msg or "expecting value" in msg or "decode" in msg or "malformed" in msg
        or "response shape" in msg or "clause array" in msg or "no usable clauses" in msg
    ):
        return "malformed_response"

    return "permanent"


def is_retryable_error(error_type: str) -> bool:
    """Determine if a given error type should be retried."""
    return error_type in ("rate_limit", "transient", "malformed_response")


# =============================================================================
# Chunk Execution & Partial-Failure Coordinator
# =============================================================================

async def execute_chunks_with_retry(
    chunks: List[DocumentChunk],
    chunk_processor: Callable[[DocumentChunk], Coroutine[Any, Any, List[Dict[str, Any]]]],
    max_retries: int = 2,
    base_backoff_seconds: float = 0.5,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process chunks sequentially with bounded retries and partial-failure preservation.

    Guarantees:
      - Successful chunks are preserved independently.
      - A failure on Chunk N does NOT discard results from Chunk 1..N-1 or N+1..M.
      - Transient / rate-limit failures retry up to max_retries with backoff.
      - Permanent errors fail fast without retry.
      - Computes deterministic completion_ratio and incomplete_chunks metadata.
      - Raises RuntimeError ONLY if ALL chunks fail.
    """
    if not chunks:
        raise ValueError("Cannot execute chunk analysis: chunk list is empty.")

    results: List[ChunkExecutionResult] = []
    all_clauses: List[Dict[str, Any]] = []

    for chunk in chunks:
        attempt = 0
        last_exc: Optional[Exception] = None
        success = False
        clauses: List[Dict[str, Any]] = []
        error_type: Optional[str] = None

        while attempt <= max_retries and not success:
            try:
                clauses = await chunk_processor(chunk)
                success = True
                break
            except Exception as exc:
                last_exc = exc
                error_type = classify_chunk_error(exc)
                attempt += 1

                if attempt <= max_retries and is_retryable_error(error_type):
                    # For rate-limits, use slightly longer backoff or match remaining cooloff
                    delay = base_backoff_seconds * (2 ** (attempt - 1))
                    if error_type == "rate_limit":
                        import re
                        m = re.search(r"([\d\.]+)\s*s\s*remaining", str(exc), re.IGNORECASE)
                        if m:
                            try:
                                rem_sec = float(m.group(1))
                                delay = min(30.0, max(delay, rem_sec + 0.5))
                            except ValueError:
                                delay = max(1.0, delay * 2)
                        else:
                            delay = max(1.0, delay * 2)
                    logger.warning(
                        f"[chunk_runner] Chunk {chunk.chunk_id} hit {error_type} (attempt {attempt}/{max_retries}). "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # Non-retryable permanent error or retries exhausted
                    logger.error(
                        f"[chunk_runner] Chunk {chunk.chunk_id} failed permanently ({error_type}): {exc}"
                    )
                    break

        exec_res = ChunkExecutionResult(
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            success=success,
            clauses=clauses if success else [],
            error_message=str(last_exc) if not success else None,
            error_type=error_type if not success else None,
            retries_attempted=max(0, attempt - 1),
        )
        results.append(exec_res)
        if success:
            all_clauses.extend(clauses)
        # Tell the UI "section N of M" (no-op unless the worker registered a callback).
        from services.progress import report_progress
        await report_progress(len(results), len(chunks))

    # ── Metadata Compilation ──────────────────────────────────────────────────
    total_chunks = len(chunks)
    successful_chunks = sum(1 for r in results if r.success)
    completion_ratio = round(successful_chunks / float(total_chunks), 4)

    incomplete_chunks = [
        {
            "chunk_id": r.chunk_id,
            "chunk_index": r.chunk_index,
            "page_start": r.page_start,
            "page_end": r.page_end,
            "error_type": r.error_type,
            "error_message": r.error_message,
        }
        for r in results
        if not r.success
    ]

    # If every chunk failed, raise a clear propagating exception
    if successful_chunks == 0:
        first_err = incomplete_chunks[0]["error_message"] if incomplete_chunks else "Unknown"
        raise RuntimeError(
            f"All {total_chunks} document chunks failed during legal analysis. First error: {first_err}"
        )

    metadata = {
        "total_chunks": total_chunks,
        "successful_chunks": successful_chunks,
        "completion_ratio": completion_ratio,
        "incomplete_chunks": incomplete_chunks,
        "is_partial": len(incomplete_chunks) > 0,
    }

    return all_clauses, metadata
