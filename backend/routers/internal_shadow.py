"""
internal_shadow.py — Operator & Telemetry Control Router (Phase 9).
Provides protected endpoints for experiment metrics, emergency kill switch control,
traffic percentage adjustment, comparison inspection, and data retention sweeps.
"""

from __future__ import annotations

import hmac
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

from database import get_db
from shadow.budget import get_shadow_budget_manager
from shadow.circuit_breaker import (
    get_dynamic_canary_percentage,
    get_dynamic_shadow_percentage,
    is_kill_switch_active,
    set_dynamic_canary_percentage,
    set_dynamic_shadow_percentage,
    set_kill_switch,
)
from shadow.config import get_shadow_settings
from shadow.retention import purge_expired_shadow_records

router = APIRouter(prefix="/internal/shadow", tags=["internal-shadow"])


# ── Operator Authorization Dependency ─────────────────────────────────────────

def verify_operator_access(
    x_shadow_admin_key: Optional[str] = Header(None, alias="X-Shadow-Admin-Key"),
):
    """
    Enforces that only internal operators with the pre-shared admin key
    can inspect shadow metrics or alter experiment traffic.
    """
    settings = get_shadow_settings()
    expected_key = settings.shadow_admin_key

    if not expected_key or not x_shadow_admin_key or not hmac.compare_digest(
        x_shadow_admin_key.encode("utf-8"), expected_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Invalid or missing X-Shadow-Admin-Key header.",
        )
    return True


# ── Request / Response Models ─────────────────────────────────────────────────

class KillSwitchRequest(BaseModel):
    active: bool
    experiment_id: Optional[str] = None


class TrafficControlRequest(BaseModel):
    shadow_percentage: Optional[float] = None
    canary_percentage: Optional[float] = None


class PurgeRequest(BaseModel):
    retention_days: Optional[int] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def get_shadow_system_status(_auth=Depends(verify_operator_access)):
    """Returns real-time operational status of the shadow and canary pipeline."""
    settings = get_shadow_settings()
    budget_mgr = get_shadow_budget_manager()

    dyn_shadow = await get_dynamic_shadow_percentage()
    dyn_canary = await get_dynamic_canary_percentage()
    kill_switch = await is_kill_switch_active(settings.shadow_experiment_id)
    daily_spend = await budget_mgr.get_daily_spend()
    cooldown = await budget_mgr.get_cooldown_remaining(settings.shadow_candidate_provider)

    return {
        "status": "active" if not kill_switch else "halted_by_kill_switch",
        "shadow_mode_enabled": settings.shadow_mode_enabled,
        "canary_mode_enabled": settings.canary_mode_enabled,
        "active_experiment_id": settings.shadow_experiment_id,
        "candidate_provider": settings.shadow_candidate_provider,
        "candidate_model": settings.shadow_candidate_model,
        "shadow_traffic_percentage": dyn_shadow if dyn_shadow is not None else settings.shadow_traffic_percentage,
        "canary_traffic_percentage": dyn_canary if dyn_canary is not None else settings.canary_traffic_percentage,
        "kill_switch_active": kill_switch,
        "daily_spend_usd": round(daily_spend, 4),
        "daily_budget_usd": settings.shadow_daily_budget_usd,
        "provider_cooldown_seconds": cooldown,
    }


@router.post("/kill-switch")
async def set_system_kill_switch(
    req: KillSwitchRequest,
    _auth=Depends(verify_operator_access),
):
    """Emergency kill switch toggle (< 500ms propagation)."""
    await set_kill_switch(experiment_id=req.experiment_id, active=req.active)
    state_str = "ACTIVATED" if req.active else "DEACTIVATED"
    target = f"experiment '{req.experiment_id}'" if req.experiment_id else "GLOBAL system"
    return {
        "message": f"Kill switch {state_str} for {target}",
        "active": req.active,
        "experiment_id": req.experiment_id,
    }


@router.post("/traffic")
async def update_traffic_allocation(
    req: TrafficControlRequest,
    _auth=Depends(verify_operator_access),
):
    """Adjusts dynamic shadow sampling and canary rollout percentages."""
    updated = {}
    if req.shadow_percentage is not None:
        await set_dynamic_shadow_percentage(req.shadow_percentage)
        updated["shadow_traffic_percentage"] = req.shadow_percentage
    if req.canary_percentage is not None:
        await set_dynamic_canary_percentage(req.canary_percentage)
        updated["canary_traffic_percentage"] = req.canary_percentage

    return {"message": "Traffic allocation updated successfully", "updated": updated}


@router.get("/metrics")
async def get_shadow_evaluation_metrics(
    experiment_id: Optional[str] = None,
    db=Depends(get_db),
    _auth=Depends(verify_operator_access),
):
    """Computes aggregate comparative accuracy, concordance, and latency statistics."""
    settings = get_shadow_settings()
    exp_id = experiment_id or settings.shadow_experiment_id

    # Aggregated query across shadow_analyses
    analyses_rows = await db.fetch(
        """SELECT execution_status, latency_ms, estimated_cost_usd, failure_category
           FROM shadow_analyses
           WHERE experiment_id = $1""",
        exp_id,
    )

    total_runs = len(analyses_rows)
    success_count = sum(1 for r in analyses_rows if r["execution_status"] == "success")
    success_rate_pct = (success_count / total_runs * 100.0) if total_runs > 0 else 0.0
    total_cost = sum(r["estimated_cost_usd"] or 0.0 for r in analyses_rows)
    avg_latency = (sum(r["latency_ms"] for r in analyses_rows) / total_runs) if total_runs > 0 else 0

    # Aggregated query across shadow_comparisons
    comp_rows = await db.fetch(
        """SELECT cer, wer, risk_concordance, citation_recall, sequence_similarity
           FROM shadow_comparisons
           WHERE experiment_id = $1""",
        exp_id,
    )

    comp_count = len(comp_rows)
    avg_cer = (sum(r["cer"] for r in comp_rows) / comp_count) if comp_count > 0 else 0.0
    avg_wer = (sum(r["wer"] for r in comp_rows) / comp_count) if comp_count > 0 else 0.0
    avg_risk_conc = (sum(r["risk_concordance"] for r in comp_rows) / comp_count) if comp_count > 0 else 0.0
    avg_cite_recall = (sum(r["citation_recall"] for r in comp_rows) / comp_count) if comp_count > 0 else 0.0
    avg_seq_sim = (sum(r["sequence_similarity"] for r in comp_rows) / comp_count) if comp_count > 0 else 0.0

    return {
        "experiment_id": exp_id,
        "total_shadow_runs": total_runs,
        "successful_runs": success_count,
        "success_rate_pct": round(success_rate_pct, 2),
        "total_spend_usd": round(total_cost, 4),
        "avg_latency_ms": int(avg_latency),
        "comparison_count": comp_count,
        "phase7_accuracy_benchmarks": {
            "avg_cer": round(avg_cer, 4),
            "avg_wer": round(avg_wer, 4),
            "avg_risk_concordance": round(avg_risk_conc, 4),
            "avg_citation_recall": round(avg_cite_recall, 4),
            "avg_sequence_similarity": round(avg_seq_sim, 4),
        },
    }


@router.get("/comparisons")
async def list_comparisons(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    experiment_id: Optional[str] = None,
    db=Depends(get_db),
    _auth=Depends(verify_operator_access),
):
    """Lists recent comparative evaluation records for analysis."""
    settings = get_shadow_settings()
    exp_id = experiment_id or settings.shadow_experiment_id

    rows = await db.fetch(
        """SELECT * FROM shadow_comparisons
           WHERE experiment_id = $1
           ORDER BY created_at DESC
           LIMIT $2 OFFSET $3""",
        exp_id, limit, offset,
    )

    return {
        "experiment_id": exp_id,
        "limit": limit,
        "offset": offset,
        "results": [dict(r) for r in rows],
    }


@router.get("/comparisons/{document_id}")
async def get_comparison_detail(
    document_id: str,
    db=Depends(get_db),
    _auth=Depends(verify_operator_access),
):
    """Retrieves full comparative diff between primary and candidate analysis for a document."""
    comp_row = await db.fetchrow(
        "SELECT * FROM shadow_comparisons WHERE document_id = $1",
        document_id,
    )
    if not comp_row:
        raise HTTPException(status_code=404, detail="Comparison record not found.")

    shadow_row = await db.fetchrow(
        "SELECT * FROM shadow_analyses WHERE document_id = $1",
        document_id,
    )
    primary_row = await db.fetchrow(
        "SELECT * FROM analyses WHERE document_id = $1",
        document_id,
    )

    return {
        "comparison": dict(comp_row),
        "candidate_analysis": json.loads(shadow_row["result_json"]) if shadow_row and shadow_row["result_json"] else None,
        "primary_analysis": json.loads(primary_row["result_json"]) if primary_row and primary_row["result_json"] else None,
    }


@router.post("/retention/purge")
async def trigger_retention_purge(
    req: PurgeRequest,
    _auth=Depends(verify_operator_access),
):
    """Immediately purges candidate analysis and comparison records older than retention threshold."""
    purged_analyses, purged_comparisons = await purge_expired_shadow_records(req.retention_days)
    return {
        "message": "Retention purge completed successfully",
        "purged_shadow_analyses": purged_analyses,
        "purged_shadow_comparisons": purged_comparisons,
    }
