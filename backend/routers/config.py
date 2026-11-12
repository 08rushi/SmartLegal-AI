from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "SmartLegal AI"

    # AI — Groq is the only provider used at runtime.
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    # Model must be one your Groq account has access to (see GET /openai/v1/models).
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")  # unused at runtime
    # Gemini vision/OCR model. Cloud vision is separately controlled by
    # CLOUD_VISION_ENABLED and PRIVACY_MODE; use the current registry default
    # whenever a key is configured so OCR does not fail on an empty model ID.
    gemini_vision_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_VISION_MODEL")

    # OpenRouter Fallback Provider (Phase 5)
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="meta-llama/llama-3.3-70b-instruct", alias="OPENROUTER_MODEL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openrouter_enabled: bool = Field(default=True, alias="OPENROUTER_ENABLED")

    # Provider Quota & Budget Policy (Phase 5)
    groq_tpm_limit: int = Field(default=8000, alias="GROQ_TPM_LIMIT")
    groq_rpm_limit: int = Field(default=30, alias="GROQ_RPM_LIMIT")
    provider_cooldown_seconds: float = Field(
        default=60.0, alias="PROVIDER_COOLDOWN_SECONDS"
    )

    # Auth
    secret_key: str = Field(default="", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    google_client_id: str = ""  # OAuth 2.0 Client ID from Google Cloud Console

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # DB — Supabase PostgreSQL in production; falls back to local SQLite when
    # DATABASE_URL is a sqlite URL or the Postgres host is unreachable.
    # Real credentials come from the .env file — never hardcode them here.
    database_url: str = Field(default="sqlite:///smartlegal.db", alias="DATABASE_URL")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Runtime environment — "production" enables durable-storage enforcement etc.
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Sentry — leave blank to disable
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    # Meta WhatsApp Cloud API (Step 3A/3B/3C/3D)
    meta_whatsapp_verify_token: str = Field(default="", alias="META_WHATSAPP_VERIFY_TOKEN")
    meta_whatsapp_access_token: str = Field(default="", alias="META_WHATSAPP_ACCESS_TOKEN")
    meta_whatsapp_app_secret: str = Field(default="", alias="META_WHATSAPP_APP_SECRET")
    meta_whatsapp_phone_number_id: str = Field(default="", alias="META_WHATSAPP_PHONE_NUMBER_ID")
    meta_whatsapp_api_version: str = Field(default="v21.0", alias="META_WHATSAPP_API_VERSION")
    meta_whatsapp_graph_url: str = Field(default="https://graph.facebook.com", alias="META_WHATSAPP_GRAPH_URL")

    # Redis — leave blank to disable (falls back to PostgreSQL-only cache)
    redis_url: str = ""
    redis_cache_ttl: int = 86400  # seconds — default 24 hours

    # Analysis jobs — a background analysis stuck in "processing" longer than this
    # (e.g. worker restarted mid-run) is reaped and marked as error.
    analysis_timeout_seconds: int = 600          # 10 minutes
    analysis_reaper_interval_seconds: int = 120  # sweep every 2 minutes

    # Password reset token lifetime.
    reset_token_expire_minutes: int = 30

    # OCR (scanned / photographed documents) — Tesseract via pytesseract.
    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    # Path to the tesseract binary if it isn't on PATH (e.g. Windows install).
    tesseract_cmd: str = Field(default="", alias="TESSERACT_CMD")
    # Languages to attempt (only those actually installed as tessdata are used).
    ocr_languages: str = Field(
        default="eng+hin+mar+tel+tam+ben+guj+kan+mal+pan+ori+urd",
        alias="OCR_LANGUAGES",
    )
    # Cap OCR to this many pages so a huge scan can't run forever.
    ocr_max_pages: int = Field(default=15, alias="OCR_MAX_PAGES")

    # Document Extraction & Routing Thresholds (Phase 2)
    page_readable_quality_threshold: float = Field(
        default=0.40, alias="PAGE_READABLE_QUALITY_THRESHOLD"
    )
    digital_min_letter_ratio: float = Field(
        default=0.40, alias="DIGITAL_MIN_LETTER_RATIO"
    )
    digital_min_letters: int = Field(
        default=20, alias="DIGITAL_MIN_LETTERS"
    )
    digital_full_prose_ratio: float = Field(
        default=0.90, alias="DIGITAL_FULL_PROSE_RATIO"
    )
    digital_length_scale_chars: int = Field(
        default=100, alias="DIGITAL_LENGTH_SCALE_CHARS"
    )
    ocr_min_confidence_threshold: float = Field(
        default=0.35, alias="OCR_MIN_CONFIDENCE_THRESHOLD"
    )

    # Visual / OCR Pipeline Configuration (Phase 4)
    privacy_mode: bool = Field(default=False, alias="PRIVACY_MODE")
    cloud_vision_enabled: bool = Field(default=True, alias="CLOUD_VISION_ENABLED")
    paddleocr_enabled: bool = Field(default=True, alias="PADDLEOCR_ENABLED")
    paddleocr_min_confidence: float = Field(default=0.40, alias="PADDLEOCR_MIN_CONFIDENCE")

    # Document Upload & Adaptive Optimization Settings (Phase 6)
    max_upload_size_mb: int = Field(default=25, alias="MAX_UPLOAD_SIZE_MB")
    max_page_count: int = Field(default=50, alias="MAX_PAGE_COUNT")
    optimization_threshold_mb: float = Field(default=8.0, alias="OPTIMIZATION_THRESHOLD_MB")
    optimization_target_mb: float = Field(default=6.0, alias="OPTIMIZATION_TARGET_MB")
    optimization_timeout_seconds: float = Field(default=15.0, alias="OPTIMIZATION_TIMEOUT_SECONDS")

    # Image Optimization Parameters (Configurable Defaults)
    optimization_target_dpi: int = Field(default=200, alias="OPTIMIZATION_TARGET_DPI")
    optimization_min_dpi: int = Field(default=150, alias="OPTIMIZATION_MIN_DPI")
    optimization_jpeg_quality: int = Field(default=85, alias="OPTIMIZATION_JPEG_QUALITY")
    optimization_color_variance_threshold: float = Field(default=12.0, alias="OPTIMIZATION_COLOR_VARIANCE_THRESHOLD")
    optimization_enabled: bool = Field(default=True, alias="OPTIMIZATION_ENABLED")

    # Technical Quality Acceptance Tolerances (Phase 6)
    optimization_text_loss_tolerance: float = Field(default=0.02, alias="OPTIMIZATION_TEXT_LOSS_TOLERANCE")
    optimization_quality_delta_tolerance: float = Field(default=0.05, alias="OPTIMIZATION_QUALITY_DELTA_TOLERANCE")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in ("production", "prod")

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown fields in .env
        case_sensitive = False  # Allow lowercase field names with UPPERCASE env vars


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    # Mask password for secure logging
    from urllib.parse import urlparse
    parsed = urlparse(settings.database_url)
    masked_url = settings.database_url
    if parsed.password:
        masked_url = settings.database_url.replace(parsed.password, "********")

    print("\n========== SETTINGS ==========")
    print("DATABASE_URL:", masked_url)
    print("==============================\n")

    return settings


def get_shadow_settings():
    from shadow.config import get_shadow_settings as _get_shadow_settings
    return _get_shadow_settings()
