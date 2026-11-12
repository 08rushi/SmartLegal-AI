"""
progress.py — tiny context-local hook so long-running analysis code can report progress
(e.g. "section 7 of 20") without threading a callback through every function signature.

The worker sets `analysis_progress` to an async callable `(done: int, total: int) -> None`
before running an analysis; the chunk executor calls it after each finished chunk.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Awaitable, Callable, Optional

ProgressCallback = Callable[[int, int], Awaitable[None]]

analysis_progress: ContextVar[Optional[ProgressCallback]] = ContextVar("analysis_progress", default=None)


async def report_progress(done: int, total: int) -> None:
    """Call the active progress callback, never letting a reporting error break the analysis."""
    cb = analysis_progress.get()
    if cb is None:
        return
    try:
        await cb(done, total)
    except Exception:  # pragma: no cover - progress is best-effort
        pass
