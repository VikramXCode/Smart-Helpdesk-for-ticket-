"""
config.py – Application settings via Pydantic BaseSettings.
All values are read from environment variables or .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/helpdesk"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── AI APIs ───────────────────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"
    JINA_API_KEY: Optional[str] = None
    JINA_MODEL: str = "jina-embeddings-v2-base-en"
    EMBEDDING_DIMENSION: int = 768

    # ── Notifications ─────────────────────────────────────────────────────────
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "helpdesk@example.com"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # ── Monitoring ────────────────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Trend Detection ───────────────────────────────────────────────────────
    TREND_MIN_CLUSTER_SIZE: int = 3
    TREND_LOOKBACK_HOURS: int = 24

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
