"""
comparison.py — Phase 7 Offline Accuracy Comparison Adapter (Phase 9).
Computes CER, WER, risk classification concordance, citation recall,
and sequence similarity between primary and candidate analysis outputs.
"""

from __future__ import annotations

import difflib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from database import get_db_ctx
from evaluation.metrics import compute_cer, compute_wer
from shadow.config import get_shadow_settings

logger = logging.getLogger("smartlegal.shadow")


class ShadowComparisonResult(BaseModel):
    """Encapsulates comparative metrics between primary and candidate results."""
    comparison_id: str
    experiment_id: str
    document_id: str
    primary_analysis_id: Optional[str]
    shadow_analysis_id: str
    cer: float
    wer: float
    risk_concordance: float
    citation_recall: float
    sequence_similarity: float
    latency_delta_ms: int
    token_delta: int
    cost_delta_usd: float
    metrics_json: Dict[str, Any] = {}


class ShadowComparisonAdapter:
    """
    Computes rigorous mathematical comparison between authoritative primary
    analysis results and experimental candidate shadow outputs using Phase 7 metrics.
    """

    @staticmethod
    def _extract_text_for_comparison(analysis_data: Dict[str, Any]) -> str:
        """Flattens clause explanations and summary into a normalized text corpus."""
        parts = []
        summary = analysis_data.get("summary", {})
        if summary.get("document_type"):
            parts.append(summary["document_type"])
        for takeaway in summary.get("key_takeaways", []):
            parts.append(takeaway)

        for clause in analysis_data.get("clauses", []):
            if clause.get("title"):
                parts.append(clause["title"])
            if clause.get("plain_english"):
                parts.append(clause["plain_english"])
            if clause.get("risk_explanation"):
                parts.append(clause["risk_explanation"])

        return " ".join(parts).strip()

    @staticmethod
    def _extract_citations(analysis_data: Dict[str, Any]) -> set[str]:
        citations = set()
        for clause in analysis_data.get("clauses", []):
            for ref in clause.get("statutory_references", []):
                if ref and isinstance(ref, str):
                    citations.add(ref.strip().lower())
        return citations

    @staticmethod
    def _compute_risk_concordance(
        primary_clauses: List[Dict[str, Any]],
        candidate_clauses: List[Dict[str, Any]],
    ) -> float:
        """
        Calculates pairwise risk level agreement across aligned clauses.
        Returns a float between 0.0 (no agreement) and 1.0 (perfect agreement).
        """
        if not primary_clauses or not candidate_clauses:
            return 1.0 if not primary_clauses and not candidate_clauses else 0.0

        min_len = min(len(primary_clauses), len(candidate_clauses))
        matches = 0
        for i in range(min_len):
            p_risk = primary_clauses[i].get("risk_level", "").lower()
            c_risk = candidate_clauses[i].get("risk_level", "").lower()
            if p_risk == c_risk:
                matches += 1

        return round(matches / float(max(len(primary_clauses), len(candidate_clauses))), 4)

    @classmethod
    async def compare_and_persist(
        cls,
        experiment_id: str,
        document_id: str,
        primary_data: Dict[str, Any],
        shadow_data: Dict[str, Any],
        shadow_analysis_id: str,
        primary_latency_ms: int = 0,
        shadow_latency_ms: int = 0,
        primary_tokens: int = 0,
        shadow_tokens: int = 0,
        shadow_cost_usd: float = 0.0,
    ) -> Optional[ShadowComparisonResult]:
        """
        Evaluates comparative metrics and persists record to shadow_comparisons.
        Runs asynchronously and will never disrupt primary workflows.
        """
        try:
            p_text = cls._extract_text_for_comparison(primary_data)
            c_text = cls._extract_text_for_comparison(shadow_data)

            # Phase 7 CER & WER calculation
            cer_res = compute_cer(p_text, c_text) if p_text else (0.0, 0)
            cer = round(float(cer_res[0] if isinstance(cer_res, tuple) else cer_res), 4)
            wer_res = compute_wer(p_text, c_text) if p_text else (0.0, 0)
            wer = round(float(wer_res[0] if isinstance(wer_res, tuple) else wer_res), 4)

            # Sequence similarity on full plain-text summaries
            matcher = difflib.SequenceMatcher(None, p_text, c_text, autojunk=False)
            seq_sim = round(float(matcher.ratio()), 4)

            # Risk classification concordance
            risk_concordance = cls._compute_risk_concordance(
                primary_data.get("clauses", []),
                shadow_data.get("clauses", []),
            )

            # Statutory citation recall / Jaccard similarity
            p_cites = cls._extract_citations(primary_data)
            c_cites = cls._extract_citations(shadow_data)
            if not p_cites and not c_cites:
                cite_recall = 1.0
            else:
                intersection = p_cites & c_cites
                union = p_cites | c_cites
                cite_recall = round(len(intersection) / float(len(union)), 4)

            # Operational Deltas
            lat_delta = shadow_latency_ms - primary_latency_ms
            tok_delta = shadow_tokens - primary_tokens
            cost_delta = round(shadow_cost_usd, 6)

            metrics_details = {
                "cer_algorithm": "difflib.SequenceMatcher",
                "primary_clause_count": len(primary_data.get("clauses", [])),
                "shadow_clause_count": len(shadow_data.get("clauses", [])),
                "primary_citations_count": len(p_cites),
                "shadow_citations_count": len(c_cites),
                "evaluation_note": "Internal engineering metrics only — not legal advice",
            }

            comparison_id = str(uuid.uuid4())
            primary_analysis_id = primary_data.get("id") or str(uuid.uuid4())

            # Persist to shadow_comparisons database table
            async with get_db_ctx() as db:
                import datetime
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                await db.execute(
                    """INSERT INTO shadow_comparisons (
                        id, experiment_id, document_id, primary_analysis_id,
                        shadow_analysis_id, cer, wer, risk_concordance,
                        citation_recall, sequence_similarity, latency_delta_ms,
                        token_delta, cost_delta_usd, metrics_json, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    )
                    ON CONFLICT (experiment_id, document_id)
                    DO UPDATE SET
                        shadow_analysis_id = EXCLUDED.shadow_analysis_id,
                        cer = EXCLUDED.cer,
                        wer = EXCLUDED.wer,
                        risk_concordance = EXCLUDED.risk_concordance,
                        citation_recall = EXCLUDED.citation_recall,
                        sequence_similarity = EXCLUDED.sequence_similarity,
                        latency_delta_ms = EXCLUDED.latency_delta_ms,
                        token_delta = EXCLUDED.token_delta,
                        cost_delta_usd = EXCLUDED.cost_delta_usd,
                        metrics_json = EXCLUDED.metrics_json,
                        created_at = EXCLUDED.created_at""",
                    comparison_id,
                    experiment_id,
                    document_id,
                    primary_analysis_id,
                    shadow_analysis_id,
                    cer,
                    wer,
                    risk_concordance,
                    cite_recall,
                    seq_sim,
                    lat_delta,
                    tok_delta,
                    cost_delta,
                    json.dumps(metrics_details),
                    now_str,
                )

            return ShadowComparisonResult(
                comparison_id=comparison_id,
                experiment_id=experiment_id,
                document_id=document_id,
                primary_analysis_id=primary_analysis_id,
                shadow_analysis_id=shadow_analysis_id,
                cer=cer,
                wer=wer,
                risk_concordance=risk_concordance,
                citation_recall=cite_recall,
                sequence_similarity=seq_sim,
                latency_delta_ms=lat_delta,
                token_delta=tok_delta,
                cost_delta_usd=cost_delta,
                metrics_json=metrics_details,
            )

        except Exception as exc:
            logger.warning("[SHADOW-COMPARISON] Comparison failed for %s: %s", document_id, exc)
            return None
