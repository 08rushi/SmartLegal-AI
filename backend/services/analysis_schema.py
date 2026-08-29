"""
Pydantic validation for AI analysis output.

The LLM returns free-form JSON; a malformed or half-empty response must never be
persisted as-is (that produces a broken analysis in the UI). `validate_analysis`
coerces every field to the expected shape, drops junk, recomputes the risk counts
from the actual clauses, and raises if the result has no usable clauses.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RiskLevel = Literal["low", "medium", "high"]


class KeyDate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str = ""
    date: str = ""


class ClauseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    title: str = ""
    original_text: str = ""
    plain_english: str = ""
    plain_hindi: str = ""
    plain_source: str = ""       # explanation in the document's own language
    source_language: str = ""    # e.g. "Marathi", "Telugu", "English"
    risk_level: RiskLevel = "medium"
    risk_score: int = 5
    risk_reason: str = ""
    clause_type: str = ""
    beneficial_to_user: bool = False
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None

    @field_validator("risk_level", mode="before")
    @classmethod
    def _norm_level(cls, v: Any) -> str:
        v = str(v).strip().lower()
        return v if v in ("low", "medium", "high") else "medium"

    @field_validator("risk_score", mode="before")
    @classmethod
    def _clamp_score(cls, v: Any) -> int:
        try:
            return max(1, min(10, int(float(v))))
        except (TypeError, ValueError):
            return 5

    @field_validator("id", "title", "original_text", "plain_english", "plain_hindi", "plain_source", "source_language", "risk_reason", "clause_type", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return "" if v is None else str(v)


class SummaryModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_type: str = "Legal Document"
    language: str = ""  # detected document language, e.g. "Marathi", "English"
    parties: list[str] = Field(default_factory=list)
    key_dates: list[KeyDate] = Field(default_factory=list)
    overall_risk: RiskLevel = "medium"
    risk_summary: str = ""
    high_risk_clauses: list[str] = Field(default_factory=list)
    beneficial_clauses: list[str] = Field(default_factory=list)
    your_obligations: list[str] = Field(default_factory=list)
    other_party_rights: list[str] = Field(default_factory=list)
    total_clauses: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0

    @field_validator("overall_risk", mode="before")
    @classmethod
    def _norm_level(cls, v: Any) -> str:
        v = str(v).strip().lower()
        return v if v in ("low", "medium", "high") else "medium"

    @field_validator("parties", "high_risk_clauses", "beneficial_clauses", "your_obligations", "other_party_rights", mode="before")
    @classmethod
    def _str_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    @field_validator("key_dates", mode="before")
    @classmethod
    def _norm_dates(cls, v: Any) -> list:
        if not isinstance(v, list):
            return []
        out = []
        for item in v:
            if isinstance(item, dict):
                out.append({"label": str(item.get("label", "")), "date": str(item.get("date", ""))})
        return out


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: SummaryModel = Field(default_factory=SummaryModel)
    clauses: list[ClauseModel] = Field(default_factory=list)


def validate_analysis(raw: dict) -> dict:
    """
    Validate & normalize a raw AI analysis dict.
    Returns a clean {summary, clauses} dict with recomputed counts.
    Raises ValueError if the response has no usable clauses.
    """
    if not isinstance(raw, dict):
        raise ValueError("Analysis result is not an object.")

    model = AnalysisModel(
        summary=raw.get("summary") or {},
        clauses=raw.get("clauses") or [],
    )

    if not model.clauses:
        raise ValueError("Analysis produced no valid clauses.")

    # Re-number clause ids that are missing/duplicated and recompute counts so the
    # summary can never disagree with the actual clause list.
    clauses = []
    for i, c in enumerate(model.clauses, start=1):
        d = c.model_dump()
        if not d.get("id"):
            d["id"] = f"clause_{i}"
        if not d.get("title"):
            d["title"] = d.get("clause_type") or f"Clause {i}"
        clauses.append(d)

    high = sum(1 for c in clauses if c["risk_level"] == "high")
    med = sum(1 for c in clauses if c["risk_level"] == "medium")
    low = sum(1 for c in clauses if c["risk_level"] == "low")

    summary = model.summary.model_dump()
    summary["total_clauses"] = len(clauses)
    summary["high_risk_count"] = high
    summary["medium_risk_count"] = med
    summary["low_risk_count"] = low

    return {"summary": summary, "clauses": clauses}
