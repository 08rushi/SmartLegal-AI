"""
checklist_service.py — Generic Checklist Engine (SL-010).

Single checklist implementation for Legal ID, Property, and Business
application domains. Replaces three nearly-identical checklist
implementations with one configurable engine.

Ownership is always validated through the parent application before
any checklist mutation is permitted.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException

from services.application_service import DOMAIN_CONFIG, _get_config, get_application


# ── Public types ─────────────────────────────────────────────────────────────

class ChecklistItem:
    """In-memory representation of a single checklist row."""
    __slots__ = ("id", "application_id", "item_text", "is_done", "updated_at")

    def __init__(self, id: str, application_id: str, item_text: str, is_done: bool, updated_at: str):
        self.id = id
        self.application_id = application_id
        self.item_text = item_text
        self.is_done = is_done
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "application_id": self.application_id,
            "item_text": self.item_text,
            "is_done": self.is_done,
            "updated_at": self.updated_at,
        }


# ── Core checklist engine ────────────────────────────────────────────────────

async def get_checklist(db, user_id: str, application_id: str, domain: str) -> list[dict]:
    """
    Retrieve the ordered checklist for an application.
    Verifies caller owns the application before returning items.
    """
    cfg = _get_config(domain)
    # Ownership check — raises 404/403 on failure
    await get_application(db, user_id, application_id, domain)

    rows = await db.fetch(
        f"SELECT id, application_id, item_text, is_done, updated_at "
        f"FROM {cfg['item_table']} WHERE application_id = $1 ORDER BY updated_at ASC",
        application_id,
    )
    return [
        ChecklistItem(
            id=r["id"],
            application_id=r["application_id"],
            item_text=r["item_text"],
            is_done=bool(r["is_done"]),
            updated_at=r["updated_at"],
        ).to_dict()
        for r in rows
    ]


async def save_checklist(
    db,
    user_id: str,
    application_id: str,
    domain: str,
    items: list[dict],          # list of {"id"?: str, "item_text": str, "is_done": bool}
) -> list[dict]:
    """
    Bulk-update checklist item completion states.
    Matches items by `id` first; falls back to `item_text` if `id` is absent.
    Ownership verified before any mutation.
    """
    cfg = _get_config(domain)
    await get_application(db, user_id, application_id, domain)

    now = datetime.utcnow().isoformat()
    for item in items:
        done_int = 1 if item.get("is_done") else 0
        if item.get("id"):
            await db.execute(
                f"UPDATE {cfg['item_table']} SET is_done=$1, updated_at=$2 "
                f"WHERE id=$3 AND application_id=$4",
                done_int, now, item["id"], application_id,
            )
        elif item.get("item_text"):
            await db.execute(
                f"UPDATE {cfg['item_table']} SET is_done=$1, updated_at=$2 "
                f"WHERE application_id=$3 AND item_text=$4",
                done_int, now, application_id, item["item_text"],
            )

    return await get_checklist(db, user_id, application_id, domain)


async def toggle_item(
    db,
    user_id: str,
    item_id: str,
    is_done: bool,
    domain: str,
) -> dict:
    """
    Toggle a single checklist item's completion state.
    Validates item exists and caller owns the parent application.
    """
    cfg = _get_config(domain)

    row = await db.fetchrow(
        f"SELECT id, application_id, item_text, is_done, updated_at FROM {cfg['item_table']} WHERE id=$1",
        item_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Checklist item not found.")

    # Ownership check via parent application
    await get_application(db, user_id, row["application_id"], domain)

    now = datetime.utcnow().isoformat()
    done_int = 1 if is_done else 0
    await db.execute(
        f"UPDATE {cfg['item_table']} SET is_done=$1, updated_at=$2 WHERE id=$3",
        done_int, now, item_id,
    )
    return ChecklistItem(
        id=row["id"],
        application_id=row["application_id"],
        item_text=row["item_text"],
        is_done=is_done,
        updated_at=now,
    ).to_dict()


async def add_checklist_item(
    db,
    user_id: str,
    application_id: str,
    domain: str,
    item_text: str,
    is_done: bool = False,
) -> dict:
    """Add a single custom checklist item to an application."""
    cfg = _get_config(domain)
    await get_application(db, user_id, application_id, domain)

    now = datetime.utcnow().isoformat()
    item_id = f"chk_{uuid.uuid4().hex[:12]}"
    done_int = 1 if is_done else 0
    await db.execute(
        f"INSERT INTO {cfg['item_table']} (id, application_id, item_text, is_done, updated_at) "
        f"VALUES ($1, $2, $3, $4, $5)",
        item_id, application_id, item_text, done_int, now,
    )
    return ChecklistItem(
        id=item_id,
        application_id=application_id,
        item_text=item_text,
        is_done=is_done,
        updated_at=now,
    ).to_dict()


async def delete_checklist_item(
    db,
    user_id: str,
    item_id: str,
    domain: str,
) -> bool:
    """Delete a single checklist item after ownership validation."""
    cfg = _get_config(domain)
    row = await db.fetchrow(
        f"SELECT id, application_id FROM {cfg['item_table']} WHERE id=$1",
        item_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Checklist item not found.")
    await get_application(db, user_id, row["application_id"], domain)
    await db.execute(f"DELETE FROM {cfg['item_table']} WHERE id=$1", item_id)
    return True


async def seed_checklist(
    db,
    application_id: str,
    domain: str,
    items: list[str],
) -> list[dict]:
    """
    Seed an application's checklist from a KB-derived text list.
    Called internally during application creation — no ownership check needed
    because the application was just created by the authenticated caller.
    """
    cfg = _get_config(domain)
    now = datetime.utcnow().isoformat()
    seeded = []
    for text in items:
        item_id = f"chk_{uuid.uuid4().hex[:12]}"
        await db.execute(
            f"INSERT INTO {cfg['item_table']} (id, application_id, item_text, is_done, updated_at) "
            f"VALUES ($1, $2, $3, 0, $4)",
            item_id, application_id, text, now,
        )
        seeded.append({"id": item_id, "application_id": application_id, "item_text": text, "is_done": False, "updated_at": now})
    return seeded
