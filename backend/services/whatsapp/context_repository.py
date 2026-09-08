"""
context_repository.py — Persistent WhatsApp Conversation & Workflow Context Repository.

Manages:
1. Durable 1-to-1 conversation context persistence per WhatsApp contact (`whatsapp_conversation_context` table).
2. Active document ID tracking & workflow states (`idle`, `document_active`, `awaiting_document_selection`, etc.).
3. Persisted candidate document selection state (`pending_candidates_json`).
4. Context status invariants (`active_document_id != NULL` => `context_status = 'active'`).
5. Contact-scoped numeric selection resolution.
"""

import datetime
import json
import logging
import uuid
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class WorkflowState:
    IDLE = "idle"
    DOCUMENT_RECEIVED = "document_received"
    DOCUMENT_ACTIVE = "document_active"
    ANALYSIS_PENDING = "analysis_pending"
    ANALYSIS_PROCESSING = "analysis_processing"
    ANALYSIS_COMPLETED = "analysis_completed"
    AWAITING_DOCUMENT_SELECTION = "awaiting_document_selection"
    AWAITING_DRAFTING_INPUT = "awaiting_drafting_input"
    DRAFTING = "drafting"
    DRAFT_READY = "draft_ready"

    ALL = (
        IDLE,
        DOCUMENT_RECEIVED,
        DOCUMENT_ACTIVE,
        ANALYSIS_PENDING,
        ANALYSIS_PROCESSING,
        ANALYSIS_COMPLETED,
        AWAITING_DOCUMENT_SELECTION,
        AWAITING_DRAFTING_INPUT,
        DRAFTING,
        DRAFT_READY,
    )


def validate_workflow_state_transition(current_state: str, next_state: str) -> str:
    """
    Centrally validate workflow state transitions.
    Normalizes invalid target states to an allowed state safely.
    """
    if next_state not in WorkflowState.ALL:
        logger.warning(f"[whatsapp-context] Invalid target state '{next_state}'. Normalizing to 'idle'.")
        return WorkflowState.IDLE
    return next_state


async def get_or_create_context(db: Any, contact_id: str) -> Dict[str, Any]:
    """
    Fetch or initialize persistent context record for contact_id.
    """
    default_ctx = {
        "id": f"ctx_{uuid.uuid4().hex[:8]}",
        "contact_id": contact_id,
        "active_document_id": None,
        "workflow_state": WorkflowState.IDLE,
        "pending_candidates_json": "[]",
        "draft_type": None,
        "draft_requirements_json": "{}",
        "draft_confirmation_status": None,
        "context_status": "cleared",
    }
    if db is None:
        return default_ctx

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        row = await db.fetchrow(
            "SELECT * FROM whatsapp_conversation_context WHERE contact_id = $1", contact_id
        )
        if row:
            return dict(row)

        ctx_id = f"ctx_{uuid.uuid4().hex[:12]}"
        await db.execute(
            """
            INSERT INTO whatsapp_conversation_context (
                id, contact_id, active_document_id, workflow_state, pending_candidates_json, context_status, created_at, updated_at
            ) VALUES ($1, $2, NULL, 'idle', '[]', 'cleared', $3, $4)
            """,
            ctx_id, contact_id, now_iso, now_iso
        )
        default_ctx["id"] = ctx_id
        default_ctx["created_at"] = now_iso
        default_ctx["updated_at"] = now_iso
        return default_ctx
    except Exception as exc:
        logger.warning(f"[whatsapp-context] Could not query/create context for contact {contact_id}: {exc}")
        return default_ctx


async def get_active_document_id(db: Any, contact_id: str) -> Optional[str]:
    """
    Resolve active document_id for contact.
    """
    ctx = await get_or_create_context(db, contact_id)
    return ctx.get("active_document_id")


async def set_active_document(
    db: Any, contact_id: str, document_id: str, workflow_state: str = "document_active"
) -> Dict[str, Any]:
    """
    Atomically set active_document_id for contact.
    Enforces invariant: context_status = 'active', clears pending_candidates_json.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ctx = await get_or_create_context(db, contact_id)

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET active_document_id = $1,
                    workflow_state = $2,
                    pending_candidates_json = '[]',
                    context_status = 'active',
                    updated_at = $3
                WHERE contact_id = $4
                """,
                document_id, workflow_state, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not update active document: {exc}")

    ctx["active_document_id"] = document_id
    ctx["workflow_state"] = workflow_state
    ctx["pending_candidates_json"] = "[]"
    ctx["context_status"] = "active"
    ctx["updated_at"] = now_iso
    return ctx


async def clear_active_document(db: Any, contact_id: str) -> Dict[str, Any]:
    """
    Atomically clear active document & context state.
    Enforces invariant: active_document_id = NULL, workflow_state = 'idle', context_status = 'cleared', pending_candidates_json = '[]'.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ctx = await get_or_create_context(db, contact_id)

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET active_document_id = NULL,
                    workflow_state = 'idle',
                    pending_candidates_json = '[]',
                    context_status = 'cleared',
                    updated_at = $1
                WHERE contact_id = $2
                """,
                now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not clear active document: {exc}")

    ctx["active_document_id"] = None
    ctx["workflow_state"] = "idle"
    ctx["pending_candidates_json"] = "[]"
    ctx["context_status"] = "cleared"
    ctx["updated_at"] = now_iso
    return ctx


async def set_pending_candidates(
    db: Any, contact_id: str, candidate_doc_ids: List[str]
) -> Dict[str, Any]:
    """
    Store pending document selection list and set workflow_state = 'awaiting_document_selection'.
    Enforces invariant: context_status = 'active'.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    candidates_json = json.dumps(candidate_doc_ids)

    # Ensure context row exists first
    ctx = await get_or_create_context(db, contact_id)

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET workflow_state = 'awaiting_document_selection',
                    pending_candidates_json = $1,
                    context_status = 'active',
                    updated_at = $2
                WHERE contact_id = $3
                """,
                candidates_json, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not set pending candidates: {exc}")

    ctx["workflow_state"] = "awaiting_document_selection"
    ctx["pending_candidates_json"] = candidates_json
    ctx["context_status"] = "active"
    ctx["updated_at"] = now_iso
    return ctx


SELECTION_EXPIRATION_SECONDS = 600  # 10 minutes


async def resolve_candidate_selection(
    db: Any, contact_id: str, index_1_based: int
) -> Optional[str]:
    """
    Resolve candidate document ID by 1-based numeric selection index.
    Checks 10-minute expiration. Lazily clears candidates if expired (> 600s).
    """
    ctx = await get_or_create_context(db, contact_id)

    if ctx.get("workflow_state") != "awaiting_document_selection":
        return None

    updated_at_str = ctx.get("updated_at")
    if updated_at_str:
        try:
            updated_dt = datetime.datetime.fromisoformat(updated_at_str)
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            if (now_dt - updated_dt).total_seconds() > SELECTION_EXPIRATION_SECONDS:
                logger.info(f"[whatsapp-context] Selection for contact_id={contact_id} expired (>10m). Clearing pending candidates.")
                await clear_active_document(db, contact_id)
                return None
        except Exception:
            pass

    raw_candidates = ctx.get("pending_candidates_json", "[]")
    try:
        candidates = json.loads(raw_candidates)
    except Exception:
        candidates = []

    if not candidates or index_1_based < 1 or index_1_based > len(candidates):
        return None

    return candidates[index_1_based - 1]


async def set_workflow_state(
    db: Any, contact_id: str, workflow_state: str
) -> Dict[str, Any]:
    """
    Update workflow state for contact.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if db is not None:
        try:
            await db.execute(
                "UPDATE whatsapp_conversation_context SET workflow_state = $1, updated_at = $2 WHERE contact_id = $3",
                workflow_state, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not set workflow state: {exc}")

    ctx = await get_or_create_context(db, contact_id)
    ctx["workflow_state"] = workflow_state
    ctx["updated_at"] = now_iso
    return ctx


async def set_drafting_state(
    db: Any,
    contact_id: str,
    draft_type: str,
    requirements: Dict[str, Any],
    workflow_state: str = WorkflowState.AWAITING_DRAFTING_INPUT,
    confirmation_status: str = "none",
) -> Dict[str, Any]:
    """
    Persist drafting workflow state and requirements.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    req_json = json.dumps(requirements)
    ctx = await get_or_create_context(db, contact_id)

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET workflow_state = $1,
                    draft_type = $2,
                    draft_requirements_json = $3,
                    draft_confirmation_status = $4,
                    context_status = 'active',
                    updated_at = $5
                WHERE contact_id = $6
                """,
                workflow_state, draft_type, req_json, confirmation_status, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not set drafting state: {exc}")

    ctx["workflow_state"] = workflow_state
    ctx["draft_type"] = draft_type
    ctx["draft_requirements_json"] = req_json
    ctx["draft_confirmation_status"] = confirmation_status
    ctx["updated_at"] = now_iso
    return ctx


async def update_draft_requirements(
    db: Any, contact_id: str, additional_reqs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge and update structured drafting requirements.
    """
    ctx = await get_or_create_context(db, contact_id)
    raw_json = ctx.get("draft_requirements_json", "{}")
    try:
        current_reqs = json.loads(raw_json)
    except Exception:
        current_reqs = {}

    current_reqs.update(additional_reqs)
    req_json = json.dumps(current_reqs)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET draft_requirements_json = $1, updated_at = $2
                WHERE contact_id = $3
                """,
                req_json, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not update draft requirements: {exc}")

    ctx["draft_requirements_json"] = req_json
    ctx["updated_at"] = now_iso
    return ctx


async def clear_drafting_state(db: Any, contact_id: str) -> Dict[str, Any]:
    """
    Clear temporary drafting workflow data and return workflow state to document_active or idle.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ctx = await get_or_create_context(db, contact_id)

    target_state = WorkflowState.DOCUMENT_ACTIVE if ctx.get("active_document_id") else WorkflowState.IDLE

    if db is not None:
        try:
            await db.execute(
                """
                UPDATE whatsapp_conversation_context
                SET workflow_state = $1,
                    draft_type = NULL,
                    draft_requirements_json = '{}',
                    draft_confirmation_status = NULL,
                    updated_at = $2
                WHERE contact_id = $3
                """,
                target_state, now_iso, contact_id
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-context] Could not clear drafting state: {exc}")

    ctx["workflow_state"] = target_state
    ctx["draft_type"] = None
    ctx["draft_requirements_json"] = "{}"
    ctx["draft_confirmation_status"] = None
    ctx["updated_at"] = now_iso
    return ctx
