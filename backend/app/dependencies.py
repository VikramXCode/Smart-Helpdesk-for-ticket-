"""
dependencies.py – FastAPI dependency injection for auth, DB sessions, and role guards.

Key dependencies:
- get_db: async SQLAlchemy session
- get_current_user: validates JWT, returns User ORM object
- require_role(*roles): factory that enforces role-based access
- company_id_from_token: extracts company_id (super admin gets None)
"""
import uuid
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import decode_access_token
from app.config import settings
from app.models import User

# ─────────────────────────────────────────────────────────────────────────────
# Database engine & session factory
# ─────────────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.ENVIRONMENT == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncSession:  # type: ignore[return]
    """Provide an async SQLAlchemy session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate JWT, return the User ORM object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# Type alias for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]


# ─────────────────────────────────────────────────────────────────────────────
# Role guards
# ─────────────────────────────────────────────────────────────────────────────

def require_role(*roles: str):
    """
    Dependency factory: raises 403 if current user's role is not in `roles`.

    Usage:
        @router.get("/admin")
        async def admin_view(user: CurrentUser = Depends(require_role("company_admin", "super_admin"))):
            ...
    """
    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return Depends(_check)


def require_super_admin():
    """Convenience: require super_admin role."""
    return require_role("super_admin")


def require_company_admin():
    """Convenience: require company_admin or super_admin role."""
    return require_role("company_admin", "super_admin")


def require_it_staff():
    """Convenience: require it_staff, company_admin, or super_admin."""
    return require_role("it_staff", "company_admin", "super_admin")


# ─────────────────────────────────────────────────────────────────────────────
# Company scoping helper
# ─────────────────────────────────────────────────────────────────────────────

def get_company_id(user: User) -> Optional[uuid.UUID]:
    """
    Return the company_id from the user.
    Super admins have no company_id (they operate platform-wide).
    """
    return user.company_id
