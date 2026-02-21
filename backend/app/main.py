"""
main.py – FastAPI application entry point.

Creates the FastAPI app with:
- Lifespan: creates DB tables on startup
- CORS middleware
- All routers registered under /api/v1/
- Exception handlers
- Optional Sentry integration
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import engine
from app.models import Base
from app.routes import auth, tickets, chat, analytics, admin, super_admin, webhooks, knowledge, issues
from app.utils.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    On startup: ensure all DB tables exist (idempotent via create_all).
    On shutdown: dispose the connection pool.
    """
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Helpdesk SaaS",
    description="Multi-tenant AI-powered IT helpdesk backend API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

register_exception_handlers(app)

# ─────────────────────────────────────────────────────────────────────────────
# Routers – all mounted under /api/v1/
# ─────────────────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(tickets.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(knowledge.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(super_admin.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(issues.router, prefix=API_PREFIX)

# ─────────────────────────────────────────────────────────────────────────────
# Optional Sentry integration
# ─────────────────────────────────────────────────────────────────────────────

if settings.SENTRY_DSN:
    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
        )
    except ImportError:
        pass  # sentry-sdk not installed


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health_check():
    """Simple health check endpoint for load balancers / uptime monitors."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
