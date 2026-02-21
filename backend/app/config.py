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
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: float = 30.0

    # ── Notifications ─────────────────────────────────────────────────────────
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "taksshinamoorthy@gmail.com"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # ── Google OAuth / Gmail ────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    GOOGLE_OAUTH_SCOPES: str = (
        "openid email profile "
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send"
    )

    # ── IMAP Email Poller (no webhooks) ───────────────────────────────────
    IMAP_POLLER_ENABLED: bool = False
    IMAP_HOST: Optional[str] = None
    IMAP_PORT: int = 993
    IMAP_USERNAME: Optional[str] = None
    IMAP_APP_PASSWORD: Optional[str] = None
    IMAP_MAILBOX: str = "INBOX"
    IMAP_USE_SSL: bool = True
    IMAP_POLL_INTERVAL_SECONDS: int = 30
    IMAP_COMPANY_ADMIN_EMAIL: Optional[str] = None

    # ── Monitoring ────────────────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    USE_MOCK_DATA: bool = False

    # ── Trend Detection ───────────────────────────────────────────────────────
    TREND_MIN_CLUSTER_SIZE: int = 3
    TREND_LOOKBACK_HOURS: int = 24

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
