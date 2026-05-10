from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "SmartLegal AI"

    # AI
    gemini_api_key: str

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore