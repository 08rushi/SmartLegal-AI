"""
config.py — Phase 9 Shadow Execution & Staged Rollout Configuration & Failure Taxonomy.
Defines runtime settings, deterministic failure codes, and rollout stages.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class FailureCategory(str, Enum):
    """Deterministic failure taxonomy for shadow execution and automated rollbacks."""
    SHADOW_TIMEOUT = "SHADOW_TIMEOUT"
    SHADOW_PROVIDER_UNAVAILABLE = "SHADOW_PROVIDER_UNAVAILABLE"
    SHADOW_RATE_LIMIT = "SHADOW_RATE_LIMIT"
    SHADOW_AUTH_FAILURE = "SHADOW_AUTH_FAILURE"
    SHADOW_CONTEXT_OVERFLOW = "SHADOW_CONTEXT_OVERFLOW"
    SHADOW_INVALID_OUTPUT = "SHADOW_INVALID_OUTPUT"
    SHADOW_INTERNAL_ERROR = "SHADOW_INTERNAL_ERROR"
    SHADOW_RESOURCE_LIMIT = "SHADOW_RESOURCE_LIMIT"
    SHADOW_CANCELLED = "SHADOW_CANCELLED"


class RolloutStage(str, Enum):
    """Disciplined staged rollout ladder for canary deployments."""
    STAGE_0_SHADOW = "stage_0_shadow"           # 0% Live (Internal shadow evaluation)
    STAGE_1_CANARY_1PCT = "stage_1_canary_1pct"   # 1% Live traffic
    STAGE_2_CANARY_5PCT = "stage_2_canary_5pct"   # 5% Live traffic
    STAGE_3_CANARY_25PCT = "stage_3_canary_25pct" # 25% Live traffic
    STAGE_4_CANARY_50PCT = "stage_4_canary_50pct" # 50% Live traffic
    STAGE_5_PRODUCTION = "stage_5_production"     # 100% Promoted to primary


class ShadowSettings(BaseSettings):
    """Pydantic v2 settings for Phase 9 Shadow Execution and Staged Canary Rollout."""
    
    # Master toggles (Default False for zero production risk)
    shadow_mode_enabled: bool = Field(default=False, alias="SHADOW_MODE_ENABLED")
    canary_mode_enabled: bool = Field(default=False, alias="CANARY_MODE_ENABLED")
    
    # Traffic sampling percentages (0.0 to 100.0)
    shadow_traffic_percentage: float = Field(default=0.0, alias="SHADOW_TRAFFIC_PERCENTAGE")
    canary_traffic_percentage: float = Field(default=0.0, alias="CANARY_TRAFFIC_PERCENTAGE")
    
    # Independent salts to prevent correlated sampling bias
    shadow_traffic_salt: str = Field(default="smartlegal_2026", alias="SHADOW_TRAFFIC_SALT")
    canary_traffic_salt: str = Field(default="smartlegal_canary_2026", alias="CANARY_TRAFFIC_SALT")
    
    # Active experiment identifier
    shadow_experiment_id: str = Field(default="exp_gemini_flash_001", alias="SHADOW_EXPERIMENT_ID")
    
    # Concurrency and timeout limits
    shadow_max_concurrency: int = Field(default=2, alias="SHADOW_MAX_CONCURRENCY")
    shadow_queue_name: str = Field(default="smartlegal:shadow_analysis", alias="SHADOW_QUEUE_NAME")
    shadow_job_timeout_seconds: int = Field(default=300, alias="SHADOW_JOB_TIMEOUT_SECONDS")
    
    # Financial and token guardrails
    shadow_daily_budget_usd: float = Field(default=10.0, alias="SHADOW_DAILY_BUDGET_USD")
    shadow_max_prompt_tokens: int = Field(default=12000, alias="SHADOW_MAX_PROMPT_TOKENS")
    shadow_max_completion_tokens: int = Field(default=4000, alias="SHADOW_MAX_COMPLETION_TOKENS")
    shadow_cost_per_million_input_tokens: float = Field(default=0.10, alias="SHADOW_COST_PER_MILLION_INPUT")
    shadow_cost_per_million_output_tokens: float = Field(default=0.40, alias="SHADOW_COST_PER_MILLION_OUTPUT")
    
    # Candidate provider configuration
    shadow_candidate_provider: str = Field(default="google_genai", alias="SHADOW_CANDIDATE_PROVIDER")
    shadow_candidate_model: str = Field(default="gemini-2.0-flash", alias="SHADOW_CANDIDATE_MODEL")
    shadow_candidate_api_key: str = Field(default="", alias="SHADOW_CANDIDATE_API_KEY")
    shadow_candidate_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="SHADOW_CANDIDATE_BASE_URL",
    )
    
    # Data hygiene and security
    shadow_retention_days: int = Field(default=30, alias="SHADOW_RETENTION_DAYS")
    # No default: the operator API stays locked (403) until SHADOW_ADMIN_KEY is set.
    shadow_admin_key: str = Field(default="", alias="SHADOW_ADMIN_KEY")
    
    # Circuit breaker thresholds
    shadow_error_rate_threshold_pct: float = Field(default=3.0, alias="SHADOW_ERROR_RATE_THRESHOLD_PCT")
    shadow_latency_degradation_ratio: float = Field(default=1.5, alias="SHADOW_LATENCY_DEGRADATION_RATIO")
    shadow_consecutive_schema_errors_limit: int = Field(default=2, alias="SHADOW_CONSECUTIVE_SCHEMA_ERRORS_LIMIT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
        populate_by_name = True


@lru_cache
def get_shadow_settings() -> ShadowSettings:
    """Return cached instance of ShadowSettings."""
    return ShadowSettings()
