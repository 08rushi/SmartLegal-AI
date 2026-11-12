"""
retention.py — Data Hygiene & PII Retention Purge Policy (Phase 9).
Purges historical candidate analysis payloads and comparison records older than 30 days.
"""

from __future__ import annotations

import datetime
import logging
from typing import Optional, Tuple

from database import get_db_ctx
from shadow.config import get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")


async def purge_expired_shadow_records(retention_days: Optional[int] = None) -> Tuple[int, int]:
    """
    Deletes shadow_analyses and shadow_comparisons records older than retention_days.
    Enforces privacy by ensuring historical legal document snapshots do not persist indefinitely.
    Returns (purged_analyses, purged_comparisons).
    """
    days = retention_days if retention_days is not None else get_shadow_settings().shadow_retention_days
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    cutoff_iso = cutoff.isoformat()

    purged_analyses = 0
    purged_comparisons = 0

    try:
        async with get_db_ctx() as db:
            # Check how many to purge
            comp_rows = await db.fetch(
                "SELECT id FROM shadow_comparisons WHERE created_at < $1",
                cutoff_iso,
            )
            purged_comparisons = len(comp_rows)

            ana_rows = await db.fetch(
                "SELECT id FROM shadow_analyses WHERE created_at < $1",
                cutoff_iso,
            )
            purged_analyses = len(ana_rows)

            if purged_comparisons > 0:
                await db.execute(
                    "DELETE FROM shadow_comparisons WHERE created_at < $1",
                    cutoff_iso,
                )

            if purged_analyses > 0:
                await db.execute(
                    "DELETE FROM shadow_analyses WHERE created_at < $1",
                    cutoff_iso,
                )

            logger.info(
                "[SHADOW-RETENTION] Purged %d expired shadow analyses and %d comparisons (cutoff: %s)",
                purged_analyses,
                purged_comparisons,
                cutoff_iso,
            )

    except Exception as exc:
        logger.warning("[SHADOW-RETENTION] Error executing data purge: %s", exc)

    return purged_analyses, purged_comparisons
