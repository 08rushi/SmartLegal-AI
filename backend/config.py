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

    # Sentry — leave blank to disable
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    # Redis — leave blank to disable (falls back to PostgreSQL-only cache)
    redis_url: str = ""
    redis_cache_ttl: int = 86400  # seconds — default 24 hours

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