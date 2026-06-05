"""
Legal ID Guidance and Tracker Router.

Provides:
1. Public endpoints: list ID types, get full guidance (no auth required)
2. Auth-protected endpoints: create/manage applications and track progress

All public endpoints (GET methods) return static guidance data.
Auth-protected endpoints implement ownership verification.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.legal_id_kb import get_all_id_types, get_id_guidance, get_id_checklist, _normalize_id_type

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    id_type: str
    service: str
    notes: str = Field(default="", max_length=5000)


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ChecklistItemCreate(BaseModel):
    id: str | None = None
    item_text: str
    is_done: bool = False


class ChecklistUpdate(BaseModel):
    items: list[ChecklistItemCreate]


class ApplicationOut(BaseModel):
    id: str
    id_type: str
    service: str
    status: str
    notes: str
    created_at: str
    updated_at: str


class ChecklistItemOut(BaseModel):
    id: str
    item_text: str
    is_done: bool
    updated_at: str


class IdTypeOut(BaseModel):
    key: str
    display_name: str
    icon: str
    authority: str
    official_portal: str


# ── Auth-Protected Routes (must come before /{id_type} catch-all) ──────────

@router.post("/applications", response_model=ApplicationOut, status_code=201)
@limiter.limit("30/minute")
async def create_application(
    request: Request,
    data: ApplicationCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Create a new application tracker for an ID service.
    Logged-in users only.
    """
    # Validate and normalize ID type
    normalized_id_type = _normalize_id_type(data.id_type)
    if not normalized_id_type:
        raise HTTPException(status_code=400, detail=f"Invalid ID type: {data.id_type}")

    guidance = get_id_guidance(normalized_id_type)
    if not guidance:
        raise HTTPException(status_code=400, detail=f"Invalid ID type: {data.id_type}")

    # Validate service exists for this ID type (case-insensitive)
    checklist = get_id_checklist(normalized_id_type, data.service)
    if checklist is None:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{data.service}' not found for ID type '{data.id_type}'"
        )

    app_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    await db.execute(
        """INSERT INTO id_applications
           (id, user_id, id_type, service, status, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (app_id, current_user["id"], normalized_id_type, data.service, "in_progress", data.notes, now, now),
    )

    # Create checklist items from knowledge base
    for item_text in checklist:
        item_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO id_checklist_items
               (id, application_id, item_text, is_done, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, app_id, item_text, 0, now),
        )

    await db.commit()

    return ApplicationOut(
        id=app_id,
        id_type=data.id_type,
        service=data.service,
        status="in_progress",
        notes=data.notes,
        created_at=now,
        updated_at=now,
    )


@router.get("/applications", response_model=dict)
@limiter.limit("60/minute")
async def list_applications(
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List all applications for the current user.
    """
    async with db.execute(
        """SELECT id, id_type, service, status, notes, created_at, updated_at
           FROM id_applications WHERE user_id = ? ORDER BY created_at DESC""",
        (current_user["id"],)
    ) as cur:
        rows = await cur.fetchall()

    applications = [
        ApplicationOut(
            id=row["id"],
            id_type=row["id_type"],
            service=row["service"],
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return {"applications": applications}


@router.get("/applications/{app_id}", response_model=ApplicationOut)
@limiter.limit("60/minute")
async def get_application(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get a specific application by ID.
    Ownership check: user can only view their own applications.
    """
    async with db.execute(
        "SELECT * FROM id_applications WHERE id = ?",
        (app_id,)
    ) as cur:
        app = await cur.fetchone()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return ApplicationOut(
        id=app["id"],
        id_type=app["id_type"],
        service=app["service"],
        status=app["status"],
        notes=app["notes"],
        created_at=app["created_at"],
        updated_at=app["updated_at"],
    )


@router.patch("/applications/{app_id}", response_model=ApplicationOut)
@limiter.limit("30/minute")
async def update_application(
    app_id: str,
    data: ApplicationUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Update an application's status or notes.
    Ownership check: user can only update their own applications.
    """
    async with db.execute(
        "SELECT * FROM id_applications WHERE id = ?",
        (app_id,)
    ) as cur:
        app = await cur.fetchone()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate status if provided
    if data.status and data.status not in ("in_progress", "submitted", "received", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status value")

    now = datetime.utcnow().isoformat()
    status = data.status if data.status else app["status"]
    notes = data.notes if data.notes is not None else app["notes"]

    await db.execute(
        "UPDATE id_applications SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
        (status, notes, now, app_id),
    )
    await db.commit()

    return ApplicationOut(
        id=app["id"],
        id_type=app["id_type"],
        service=app["service"],
        status=status,
        notes=notes,
        created_at=app["created_at"],
        updated_at=now,
    )


@router.delete("/applications/{app_id}")
@limiter.limit("30/minute")
async def delete_application(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Delete an application and its checklist items.
    Ownership check: user can only delete their own applications.
    """
    async with db.execute(
        "SELECT * FROM id_applications WHERE id = ?",
        (app_id,)
    ) as cur:
        app = await cur.fetchone()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete checklist items first
    await db.execute("DELETE FROM id_checklist_items WHERE application_id = ?", (app_id,))

    # Delete application
    await db.execute("DELETE FROM id_applications WHERE id = ?", (app_id,))
    await db.commit()

    return {"message": "Application deleted"}


@router.get("/applications/{app_id}/checklist")
@limiter.limit("60/minute")
async def get_checklist(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get checklist items for an application.
    Ownership check: user can only view their own application's checklist.
    """
    # Verify ownership
    async with db.execute(
        "SELECT user_id FROM id_applications WHERE id = ?",
        (app_id,)
    ) as cur:
        app = await cur.fetchone()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch checklist items
    async with db.execute(
        "SELECT id, item_text, is_done, updated_at FROM id_checklist_items WHERE application_id = ?",
        (app_id,)
    ) as cur:
        items = await cur.fetchall()

    return {
        "application_id": app_id,
        "items": [
            ChecklistItemOut(
                id=item["id"],
                item_text=item["item_text"],
                is_done=bool(item["is_done"]),
                updated_at=item["updated_at"],
            )
            for item in items
        ],
    }


@router.post("/applications/{app_id}/checklist")
@limiter.limit("30/minute")
async def save_checklist(
    app_id: str,
    data: ChecklistUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Update checklist item progress for an application.
    Ownership check: user can only update their own application's checklist.
    """
    # Verify ownership
    async with db.execute(
        "SELECT user_id FROM id_applications WHERE id = ?",
        (app_id,)
    ) as cur:
        app = await cur.fetchone()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.utcnow().isoformat()

    # Update each item using id (preferred) or item_text (fallback)
    for item in data.items:
        if item.id:
            await db.execute(
                "UPDATE id_checklist_items SET is_done = ?, updated_at = ? WHERE id = ? AND application_id = ?",
                (1 if item.is_done else 0, now, item.id, app_id),
            )
        else:
            await db.execute(
                "UPDATE id_checklist_items SET is_done = ?, updated_at = ? WHERE application_id = ? AND item_text = ?",
                (1 if item.is_done else 0, now, app_id, item.item_text),
            )

    await db.commit()

    # Return updated checklist
    async with db.execute(
        "SELECT id, item_text, is_done, updated_at FROM id_checklist_items WHERE application_id = ?",
        (app_id,)
    ) as cur:
        items = await cur.fetchall()

    return {
        "application_id": app_id,
        "items": [
            ChecklistItemOut(
                id=item["id"],
                item_text=item["item_text"],
                is_done=bool(item["is_done"]),
                updated_at=item["updated_at"],
            )
            for item in items
        ],
    }


# ── Public Routes (no auth required) ───────────────────────────────────────

@router.get("/", response_model=dict)
@limiter.limit("100/minute")
async def list_id_types(request: Request):
    """
    List all 6 supported government ID types.
    Returns summary data for frontend hub card grid.
    """
    return {"id_types": get_all_id_types()}


@router.get("/{id_type}")
@limiter.limit("100/minute")
async def get_guidance(request: Request, id_type: str):
    """
    Get full guidance for one ID type.
    Includes services, fees, timelines, FAQs, legal protections.
    """
    guidance = get_id_guidance(id_type)
    if not guidance:
        raise HTTPException(status_code=404, detail=f"ID type '{id_type}' not found")

    return {"guidance": guidance}
