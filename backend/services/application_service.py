"""
application_service.py — Unified Generic Service & Application Platform.

Provides a unified, domain-configurable CRUD & checklist platform for
Legal ID, Property, Business License, and Jan-Yojana civic service applications.
Replaces domain-duplicated SQL logic with single-source-of-truth authorization.
"""

import uuid
from datetime import datetime
from fastapi import HTTPException

DOMAIN_CONFIG = {
    "legal-id": {
        "app_table": "id_applications",
        "item_table": "id_checklist_items",
        "type_column": "id_type"
    },
    "property": {
        "app_table": "property_applications",
        "item_table": "property_checklist_items",
        "type_column": "property_type"
    },
    "business": {
        "app_table": "business_applications",
        "item_table": "business_checklist_items",
        "type_column": "business_type"
    }
}


def _get_config(domain: str) -> dict:
    config = DOMAIN_CONFIG.get(domain.lower())
    if not config:
        raise HTTPException(status_code=400, detail=f"Unsupported service domain '{domain}'")
    return config


async def create_application(
    db,
    user_id: str,
    domain: str,
    type_key: str,
    service: str,
    notes: str = "",
    default_items: list[str] | None = None
) -> dict:
    """Generic creator for Legal ID, Property, or Business applications."""
    cfg = _get_config(domain)
    app_id = f"app_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    query = f"""
        INSERT INTO {cfg['app_table']} (id, user_id, {cfg['type_column']}, service, status, notes, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    await db.execute(query, app_id, user_id, type_key, service, "in_progress", notes, now, now)

    # Seed default checklist items if provided
    items = []
    if default_items:
        for text in default_items:
            item_id = f"chk_{uuid.uuid4().hex[:12]}"
            await db.execute(
                f"INSERT INTO {cfg['item_table']} (id, application_id, item_text, is_done, updated_at) VALUES ($1, $2, $3, 0, $4)",
                item_id, app_id, text, now
            )
            items.append({"id": item_id, "application_id": app_id, "item_text": text, "is_done": 0, "updated_at": now})

    return {
        "id": app_id,
        "user_id": user_id,
        "domain": domain,
        "type_key": type_key,
        "service": service,
        "status": "in_progress",
        "notes": notes,
        "created_at": now,
        "updated_at": now,
        "checklist": items
    }


async def list_applications(db, user_id: str, domain: str) -> list[dict]:
    """Generic lister for user's applications in a given domain."""
    cfg = _get_config(domain)
    query = f"SELECT * FROM {cfg['app_table']} WHERE user_id = $1 ORDER BY updated_at DESC"
    rows = await db.fetch(query, user_id)
    return [dict(r) for r in rows]


async def get_application(db, user_id: str, application_id: str, domain: str) -> dict:
    """Generic ownership-verified application retriever."""
    cfg = _get_config(domain)
    query = f"SELECT * FROM {cfg['app_table']} WHERE id = $1 AND user_id = $2"
    row = await db.fetchrow(query, application_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found or unauthorized.")
    
    app = dict(row)
    # Fetch checklist items
    items = await db.fetch(f"SELECT * FROM {cfg['item_table']} WHERE application_id = $1 ORDER BY updated_at ASC", application_id)
    app["checklist"] = [dict(i) for i in items]
    return app


async def update_application(db, user_id: str, application_id: str, domain: str, status: str | None = None, notes: str | None = None) -> dict:
    """Generic status and notes updater."""
    cfg = _get_config(domain)
    # Verify ownership
    await get_application(db, user_id, application_id, domain)

    now = datetime.utcnow().isoformat()
    if status and notes is not None:
        await db.execute(f"UPDATE {cfg['app_table']} SET status = $1, notes = $2, updated_at = $3 WHERE id = $4", status, notes, now, application_id)
    elif status:
        await db.execute(f"UPDATE {cfg['app_table']} SET status = $1, updated_at = $2 WHERE id = $3", status, now, application_id)
    elif notes is not None:
        await db.execute(f"UPDATE {cfg['app_table']} SET notes = $1, updated_at = $2 WHERE id = $3", notes, now, application_id)

    return await get_application(db, user_id, application_id, domain)


async def delete_application(db, user_id: str, application_id: str, domain: str) -> bool:
    """Generic deleter for applications and associated checklists."""
    cfg = _get_config(domain)
    await get_application(db, user_id, application_id, domain)
    
    # Delete child items first (or rely on ON DELETE CASCADE)
    await db.execute(f"DELETE FROM {cfg['item_table']} WHERE application_id = $1", application_id)
    await db.execute(f"DELETE FROM {cfg['app_table']} WHERE id = $1 AND user_id = $2", application_id, user_id)
    return True


async def toggle_checklist_item(db, user_id: str, item_id: str, is_done: bool, domain: str) -> dict:
    """Generic checklist toggle item executor."""
    cfg = _get_config(domain)
    now = datetime.utcnow().isoformat()
    
    # Verify item exists
    row = await db.fetchrow(f"SELECT * FROM {cfg['item_table']} WHERE id = $1", item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Checklist item not found.")

    item = dict(row)
    # Verify application ownership
    await get_application(db, user_id, item["application_id"], domain)

    await db.execute(f"UPDATE {cfg['item_table']} SET is_done = $1, updated_at = $2 WHERE id = $3", 1 if is_done else 0, now, item_id)
    item["is_done"] = 1 if is_done else 0
    item["updated_at"] = now
    return item
