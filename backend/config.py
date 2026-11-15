import os

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "SmartLegal AI"

    # AI — Groq is the only provider used at runtime.
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    # Model must be one your Groq account has access to (see GET /openai/v1/models).
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    groq_stt_model: str = Field(default="whisper-large-v3", alias="GROQ_STT_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")  # unused at runtime
    # Gemini vision/OCR model. Cloud vision is separately controlled by
    # CLOUD_VISION_ENABLED and PRIVACY_MODE; use the current registry default
    # whenever a key is configured so OCR does not fail on an empty model ID.
    # gemini-2.5-flash: stable GA model, 1M context, strong on handwriting, cheap on the paid tier.
    gemini_vision_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_VISION_MODEL")
    # Model for whole-document analysis (empty = use gemini-2.5-flash). Use gemini-2.5-flash-lite to cut cost further.
    gemini_text_model: str = Field(default="", alias="GEMINI_TEXT_MODEL")
    # Which engine analyses documents: "auto" (Gemini for long documents when usable, else Groq),
    # "gemini" (Gemini whenever usable) or "groq" (never use Gemini for analysis).
    analysis_provider: str = Field(default="auto", alias="ANALYSIS_PROVIDER")
    # Pages sent to Gemini Vision per request when reading scans / handwriting.
    vision_batch_pages: int = Field(default=4, alias="VISION_BATCH_PAGES")
    # Comma-separated emails allowed to use admin-only endpoints (e.g. scheme ingestion). Empty = disabled.
    admin_emails: str = Field(default="", alias="ADMIN_EMAILS")

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
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    # DEPRECATED: the credential is the HttpOnly sl_token cookie. When true, login/register/google
    # also return `access_token` in the JSON body (only for the legacy frontend during migration).
    auth_return_body_token: bool = Field(default=False, alias="AUTH_RETURN_BODY_TOKEN")
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

    # Runtime environment. FAIL-CLOSED: anything other than development/dev/test/testing/local
    # (including unset) is treated as production. Dev-only behaviours require ENVIRONMENT=development.
    environment: str = Field(default="production", alias="ENVIRONMENT")
    # Dev convenience: return the password-reset token in the /forgot-password response.
    # Honoured ONLY when ENVIRONMENT is a development value AND this is true.
    expose_reset_token_in_response: bool = Field(default=False, alias="EXPOSE_RESET_TOKEN_IN_RESPONSE")

    # Sentry — leave blank to disable
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    # WhatsApp bot is NOT integrated yet — router is only mounted when this is true.
    whatsapp_enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")

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
    # Big documents get more time: timeout = clamp(120 + pages * seconds_per_page, base, max).
    # (Free-tier LLM limits make long documents slow but still completable.)
    analysis_seconds_per_page: int = 90
    analysis_max_timeout_seconds: int = 3600     # 1 hour hard ceiling

    # Password reset token lifetime.
    reset_token_expire_minutes: int = 30

    # Transactional email via Resend (https://resend.com). Blank key = email disabled.
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    # Verified sender, e.g. "SmartLegal AI <no-reply@yourdomain.com>".
    email_from: str = Field(default="", alias="EMAIL_FROM")
    # Public frontend base URL used to build links in emails.
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    # Optional SMTP sender (e.g. a Gmail app password) for hosts without a verified Resend domain.
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")

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

    # Whether startup runs create_tables() DDL. Unset (blank) = auto: true for
    # SQLite/dev, false for production + Postgres (schema then governed by Alembic).
    auto_create_schema: Optional[bool] = Field(default=None, alias="AUTO_CREATE_SCHEMA")

    @field_validator("auto_create_schema", mode="before")
    @classmethod
    def _blank_auto_create_schema(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @property
    def is_sqlite_url(self) -> bool:
        return self.database_url.strip().lower().startswith("sqlite")

    @property
    def effective_auto_create_schema(self) -> bool:
        if self.auto_create_schema is not None:
            return self.auto_create_schema
        return not (self.is_production and not self.is_sqlite_url)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() in ("development", "dev", "test", "testing", "local")

    @property
    def is_production(self) -> bool:
        # Fail-closed: not explicitly a development environment => production rules apply.
        return not self.is_development

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown fields in .env
        case_sensitive = False  # Allow lowercase field names with UPPERCASE env vars


_INSECURE_SECRET_MARKERS = (
    "changeme", "change-me", "change_me", "secret", "password", "your-", "your_",
    "example", "placeholder", "default", "insecure",
)


def validate_production_config(s: "Settings") -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a production deployment. Never includes secret values."""
    errors: list[str] = []
    warnings: list[str] = []
    if not s.is_production:
        return errors, warnings

    key = s.secret_key or ""
    if len(key) < 32:
        errors.append("SECRET_KEY must be set to a random value of at least 32 characters "
                      "(e.g. `openssl rand -hex 32`).")
    elif any(m in key.lower() for m in _INSECURE_SECRET_MARKERS) or len(set(key)) < 8:
        errors.append("SECRET_KEY looks like a placeholder/insecure value; generate a random one.")

    if not (s.database_url or "").strip():
        errors.append("DATABASE_URL is not set.")
    elif s.is_sqlite_url:
        errors.append("DATABASE_URL points at SQLite; production requires a Postgres DATABASE_URL.")

    origins = [o.strip() for o in (s.allowed_origins or "").split(",") if o.strip()]
    if not origins:
        errors.append("ALLOWED_ORIGINS is not set (comma-separated list of frontend origins).")
    elif "*" in origins:
        errors.append("ALLOWED_ORIGINS must not contain '*' in production.")
    elif all(("localhost" in o or "127.0.0.1" in o) for o in origins):
        errors.append("ALLOWED_ORIGINS only contains localhost origins; set the real frontend origin(s).")

    if not all((s.cloudinary_cloud_name, s.cloudinary_api_key, s.cloudinary_api_secret)):
        errors.append("Cloudinary (CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET) is required in production; "
                      "local file storage is not durable.")

    if not s.sentry_dsn:
        warnings.append("SENTRY_DSN is not set; error monitoring is disabled.")
    if not (s.resend_api_key and s.email_from) and not (s.smtp_host and s.smtp_user and s.smtp_password):
        warnings.append("No email sender configured (RESEND_API_KEY+EMAIL_FROM or SMTP_*); "
                        "password-reset emails will not be sent.")
    if not s.redis_url:
        warnings.append("REDIS_URL is not set; no L1 cache and analysis jobs run inline (no durable queue).")
    if "localhost" in (s.frontend_url or "") or "127.0.0.1" in (s.frontend_url or ""):
        warnings.append("FRONTEND_URL points at localhost; email links will be wrong.")
    return errors, warnings


def _platform_public_url() -> str:
    """Public URL the hosting platform assigned to this service (Render / Koyeb), or ''."""
    url = (os.environ.get("RENDER_EXTERNAL_URL") or "").strip()
    if not url and os.environ.get("KOYEB_PUBLIC_DOMAIN"):
        url = "https://" + os.environ["KOYEB_PUBLIC_DOMAIN"].strip()
    return url.rstrip("/")


def _apply_platform_url(s: "Settings") -> None:
    """When the platform tells us our public URL, trust it as the (same-origin) frontend origin
    so ALLOWED_ORIGINS / FRONTEND_URL need no manual edit after the first deploy."""
    url = _platform_public_url()
    if not url:
        return
    origins = [o.strip() for o in (s.allowed_origins or "").split(",") if o.strip()]
    if url not in origins:
        origins = [o for o in origins if "localhost" not in o and "127.0.0.1" not in o] + [url]
        s.allowed_origins = ",".join(origins)
    if "localhost" in (s.frontend_url or "") or "127.0.0.1" in (s.frontend_url or ""):
        s.frontend_url = url


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _apply_platform_url(settings)

    errors, warnings = validate_production_config(settings)
    for w in warnings:
        print(f"[config] WARNING: {w}")
    if errors:
        raise RuntimeError(
            "Invalid production configuration:\n  - " + "\n  - ".join(errors)
        )

    # JWT signing key: refuse to boot in production without a strong one;
    # warn loudly in development.
    if len(settings.secret_key) < 32:
        if settings.is_production:
            raise RuntimeError(
                "SECRET_KEY must be set to a random value of at least 32 characters "
                "in production (e.g. `openssl rand -hex 32`)."
            )
        print("[config] WARNING: SECRET_KEY is empty or shorter than 32 chars — "
              "set a strong value in backend/.env (required in production).")

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
