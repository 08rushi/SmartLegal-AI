from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "SmartLegal AI"

    # AI — Groq is primary, Gemini is optional fallback
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # Auth
    secret_key: str = Field(default="", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    google_client_id: str = ""  # OAuth 2.0 Client ID from Google Cloud Console

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # DB
    database_url: str = "sqlite:///./smartlegal.db"

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Sentry — leave blank to disable
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    # Redis — leave blank to disable (falls back to SQLite-only cache)
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
    return Settings()  # type: ignore