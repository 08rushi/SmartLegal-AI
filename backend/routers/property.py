"""
Property Hub Guidance Router.

Provides:
1. Public endpoints: list property types, get full guidance (no auth required)
2. Auth-protected endpoints: create/manage property applications and track progress

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
from services.property_kb import get_all_property_types, get_property_guidance, get_property_checklist, _normalize_property_type

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class PropertyApplicationCreate(BaseModel):
    property_type: str
    service: str
    notes: str = Field(default="", max_length=5000)


class PropertyApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ChecklistItemCreate(BaseModel):
    id: str | None = None
    item_text: str
    is_done: bool = False


class ChecklistUpdate(BaseModel):
    items: list[ChecklistItemCreate]


class PropertyApplicationOut(BaseModel):
    id: str
    property_type: str
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


class PropertyTypeOut(BaseModel):
    key: str
    display_name: str
    icon: str
    authority: str
    official_portal: str


# ── Auth-Protected Routes (must come before /{property_type} catch-all) ────

@router.post("/applications", response_model=PropertyApplicationOut, status_code=201)
@limiter.limit("30/minute")
async def create_application(
    request: Request,
    data: PropertyApplicationCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Create a new property service application tracker.
    Logged-in users only.
    """
    # Validate and normalize property type
    normalized_property_type = _normalize_property_type(data.property_type)
    if not normalized_property_type:
        raise HTTPException(status_code=400, detail=f"Invalid property type: {data.property_type}")

    guidance = get_property_guidance(normalized_property_type)
    if not guidance:
        raise HTTPException(status_code=400, detail=f"Invalid property type: {data.property_type}")

    # Validate service exists for this property type (case-insensitive)
    checklist = get_property_checklist(normalized_property_type, data.service)
    if checklist is None:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{data.service}' not found for property type '{data.property_type}'"
        )

    app_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    await db.execute(
        """INSERT INTO property_applications
           (id, user_id, property_type, service, status, notes, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        app_id, current_user["id"], normalized_property_type, data.service, "in_progress", data.notes, now, now,
    )

    # Create checklist items from knowledge base
    for item_text in checklist:
        item_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO property_checklist_items
               (id, application_id, item_text, is_done, updated_at)
               VALUES ($1, $2, $3, $4, $5)""",
            item_id, app_id, item_text, 0, now,
        )

    return PropertyApplicationOut(
        id=app_id,
        property_type=data.property_type,
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
    List all property applications for the current user.
    """
    rows = await db.fetch(
        """SELECT id, property_type, service, status, notes, created_at, updated_at
           FROM property_applications WHERE user_id = $1 ORDER BY created_at DESC""",
        current_user["id"],
    )

    applications = [
        PropertyApplicationOut(
            id=row["id"],
            property_type=row["property_type"],
            service=row["service"],
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return {"applications": applications}


@router.get("/applications/{app_id}", response_model=PropertyApplicationOut)
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
    app = await db.fetchrow(
        "SELECT * FROM property_applications WHERE id = $1",
        app_id,
    )

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return PropertyApplicationOut(
        id=app["id"],
        property_type=app["property_type"],
        service=app["service"],
        status=app["status"],
        notes=app["notes"],
        created_at=app["created_at"],
        updated_at=app["updated_at"],
    )


@router.patch("/applications/{app_id}", response_model=PropertyApplicationOut)
@limiter.limit("30/minute")
async def update_application(
    app_id: str,
    data: PropertyApplicationUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Update an application's status or notes.
    Ownership check: user can only update their own applications.
    """
    app = await db.fetchrow(
        "SELECT * FROM property_applications WHERE id = $1",
        app_id,
    )

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
        "UPDATE property_applications SET status = $1, notes = $2, updated_at = $3 WHERE id = $4",
        status, notes, now, app_id,
    )

    return PropertyApplicationOut(
        id=app["id"],
        property_type=app["property_type"],
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
    app = await db.fetchrow(
        "SELECT * FROM property_applications WHERE id = $1",
        app_id,
    )

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete checklist items first
    await db.execute("DELETE FROM property_checklist_items WHERE application_id = $1", app_id,)

    # Delete application
    await db.execute("DELETE FROM property_applications WHERE id = $1", app_id,)

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
    app = await db.fetchrow(
        "SELECT user_id FROM property_applications WHERE id = $1",
        app_id,
    )

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch checklist items
    items = await db.fetch(
        "SELECT id, item_text, is_done, updated_at FROM property_checklist_items WHERE application_id = $1",
        app_id,
    )

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
    app = await db.fetchrow(
        "SELECT user_id FROM property_applications WHERE id = $1",
        app_id,
    )

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.utcnow().isoformat()

    # Update each item using id (preferred) or item_text (fallback)
    for item in data.items:
        if item.id:
            await db.execute(
                "UPDATE property_checklist_items SET is_done = $1, updated_at = $2 WHERE id = $3 AND application_id = $4",
                1 if item.is_done else 0, now, item.id, app_id,
            )
        else:
            await db.execute(
                "UPDATE property_checklist_items SET is_done = $1, updated_at = $2 WHERE application_id = $3 AND item_text = $4",
                1 if item.is_done else 0, now, app_id, item.item_text,
            )

    # Return updated checklist
    items = await db.fetch(
        "SELECT id, item_text, is_done, updated_at FROM property_checklist_items WHERE application_id = $1",
        app_id,
    )

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
async def list_property_types(request: Request):
    """
    List all 5 supported property transaction types.
    Returns summary data for frontend hub card grid.
    """
    return {"property_types": get_all_property_types()}


@router.get("/{property_type}")
@limiter.limit("100/minute")
async def get_guidance(request: Request, property_type: str):
    """
    Get full guidance for one property type.
    Includes services, fees, timelines, FAQs, legal protections.
    """
    guidance = get_property_guidance(property_type)
    if not guidance:
        raise HTTPException(status_code=404, detail=f"Property type '{property_type}' not found")

    return {"guidance": guidance}
