"""
Legal ID Guidance and Tracker Router  (SL-009 / SL-011 refactor).

HTTP-adapter layer — all business logic lives in:
  services.application_service  (application CRUD + ownership)
  services.checklist_service    (checklist engine)
  services.legal_id_kb          (knowledge-base / guidance data)

This router only:
  • Validates HTTP input (Pydantic schemas)
  • Calls the appropriate service function
  • Maps the result to an HTTP response
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from database import get_db
from limiter import limiter
from routers.auth import get_current_user
from services.legal_id_kb import (
    get_all_id_types, get_id_guidance, get_id_checklist, _normalize_id_type,
)
from services.application_service import (
    create_application as svc_create,
    list_applications as svc_list,
    get_application as svc_get,
    update_application as svc_update,
    delete_application as svc_delete,
)
from services.checklist_service import (
    get_checklist as svc_checklist_get,
    save_checklist as svc_checklist_save,
    seed_checklist,
)

router = APIRouter()

DOMAIN = "legal-id"
VALID_STATUSES = {"in_progress", "submitted", "received", "completed"}


# ── Request / Response Schemas ────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_app_out(app: dict) -> ApplicationOut:
    return ApplicationOut(
        id=app["id"],
        id_type=app.get("id_type", app.get("type_key", "")),
        service=app["service"],
        status=app["status"],
        notes=app.get("notes", ""),
        created_at=app["created_at"],
        updated_at=app["updated_at"],
    )


def _to_checklist_out(items: list[dict]) -> list[ChecklistItemOut]:
    return [
        ChecklistItemOut(
            id=it["id"],
            item_text=it["item_text"],
            is_done=bool(it["is_done"]),
            updated_at=it["updated_at"],
        )
        for it in items
    ]


# ── Auth-Protected Routes ─────────────────────────────────────────────────────

@router.post("/applications", response_model=ApplicationOut, status_code=201)
@limiter.limit("30/minute")
async def create_application(
    request: Request,
    data: ApplicationCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a new Legal ID application tracker (authenticated users only)."""
    normalized = _normalize_id_type(data.id_type)
    if not normalized or not get_id_guidance(normalized):
        raise HTTPException(status_code=400, detail=f"Invalid ID type: {data.id_type}")

    checklist_items = get_id_checklist(normalized, data.service)
    if checklist_items is None:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{data.service}' not found for ID type '{data.id_type}'",
        )

    app = await svc_create(
        db,
        user_id=current_user["id"],
        domain=DOMAIN,
        type_key=normalized,
        service=data.service,
        notes=data.notes,
    )
    await seed_checklist(db, app["id"], DOMAIN, checklist_items)
    app["id_type"] = app.get("type_key", normalized)
    return _to_app_out(app)


@router.get("/applications", response_model=dict)
@limiter.limit("60/minute")
async def list_applications(
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """List all Legal ID applications for the current user."""
    apps = await svc_list(db, user_id=current_user["id"], domain=DOMAIN)
    return {"applications": [_to_app_out(a) for a in apps]}


@router.get("/applications/{app_id}", response_model=ApplicationOut)
@limiter.limit("60/minute")
async def get_application(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Get a specific Legal ID application (ownership enforced)."""
    app = await svc_get(db, user_id=current_user["id"], application_id=app_id, domain=DOMAIN)
    return _to_app_out(app)


@router.patch("/applications/{app_id}", response_model=ApplicationOut)
@limiter.limit("30/minute")
async def update_application(
    app_id: str,
    data: ApplicationUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Update a Legal ID application's status or notes (ownership enforced)."""
    if data.status and data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status value")
    app = await svc_update(
        db,
        user_id=current_user["id"],
        application_id=app_id,
        domain=DOMAIN,
        status=data.status,
        notes=data.notes,
    )
    return _to_app_out(app)


@router.delete("/applications/{app_id}")
@limiter.limit("30/minute")
async def delete_application(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a Legal ID application and its checklist (ownership enforced)."""
    await svc_delete(db, user_id=current_user["id"], application_id=app_id, domain=DOMAIN)
    return {"message": "Application deleted"}


@router.get("/applications/{app_id}/checklist")
@limiter.limit("60/minute")
async def get_checklist(
    app_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Return checklist items for a Legal ID application (ownership enforced)."""
    items = await svc_checklist_get(db, user_id=current_user["id"], application_id=app_id, domain=DOMAIN)
    return {"application_id": app_id, "items": _to_checklist_out(items)}


@router.post("/applications/{app_id}/checklist")
@limiter.limit("30/minute")
async def save_checklist(
    app_id: str,
    data: ChecklistUpdate,
    request: Request,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Bulk-update checklist completion states for a Legal ID application."""
    items = await svc_checklist_save(
        db,
        user_id=current_user["id"],
        application_id=app_id,
        domain=DOMAIN,
        items=[it.model_dump() for it in data.items],
    )
    return {"application_id": app_id, "items": _to_checklist_out(items)}


# ── Public Routes ─────────────────────────────────────────────────────────────

@router.get("/", response_model=dict)
@limiter.limit("100/minute")
async def list_id_types(request: Request):
    """List all 6 supported government ID types (no auth required)."""
    return {"id_types": get_all_id_types()}


@router.get("/{id_type}")
@limiter.limit("100/minute")
async def get_guidance(request: Request, id_type: str):
    """Get full guidance for one ID type (no auth required)."""
    guidance = get_id_guidance(id_type)
    if not guidance:
        raise HTTPException(status_code=404, detail=f"ID type '{id_type}' not found")
    return {"guidance": guidance}
