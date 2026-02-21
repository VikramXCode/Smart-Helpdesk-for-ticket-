"""
routes/auth.py – Authentication endpoints.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, hash_password, verify_password
from app.config import settings
from app.dependencies import CurrentUser, DB, get_db
from app.models import AuditLog, Company, User
from app.schemas import (
    ChangePasswordRequest,
    GoogleAuthUrlResponse,
    GoogleOAuthCallbackResponse,
    LoginRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DEFAULT_INITIAL_PASSWORD = "12345678"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _ensure_google_oauth_configured() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )


def _create_google_oauth_state(user_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "type": "google_oauth_state",
        "nonce": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_google_oauth_state(state_token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(state_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "google_oauth_state" or not payload.get("sub"):
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
        return uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DB):
    """
    Authenticate user and return a JWT token.
    The token payload includes user_id, company_id, and role.
    """
    # Find user by email (super admin has no company constraint)
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_change_required = (
        user.role in ("company_admin", "it_staff", "employee")
        and verify_password(DEFAULT_INITIAL_PASSWORD, user.hashed_password)
    )

    # Fetch company name for the response
    company_name = None
    company_slug = None
    if user.company_id:
        company_result = await db.execute(
            select(Company).where(Company.id == user.company_id)
        )
        company = company_result.scalar_one_or_none()
        if company:
            company_name = company.name
            company_slug = company.slug

    # Create JWT
    token = create_access_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role,
    )

    # Audit log
    db.add(AuditLog(
        company_id=user.company_id,
        user_id=user.id,
        action="user_login",
        details={"email": user.email, "role": user.role},
    ))
    await db.commit()

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        company_name=company_name,
        company_slug=company_slug,
        team_id=user.team_id,
        avatar_url=user.avatar_url,
        status=user.status,
        department=user.department,
        password_change_required=password_change_required,
    )

    return TokenResponse(
        access_token=token,
        user=user_out,
        password_change_required=password_change_required,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser, db: DB):
    """Return the currently authenticated user's profile."""
    company_name = None
    company_slug = None
    if current_user.company_id:
        company_result = await db.execute(
            select(Company).where(Company.id == current_user.company_id)
        )
        company = company_result.scalar_one_or_none()
        if company:
            company_name = company.name
            company_slug = company.slug

    password_change_required = (
        current_user.role in ("company_admin", "it_staff", "employee")
        and verify_password(DEFAULT_INITIAL_PASSWORD, current_user.hashed_password)
    )

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        company_id=current_user.company_id,
        company_name=company_name,
        company_slug=company_slug,
        team_id=current_user.team_id,
        avatar_url=current_user.avatar_url,
        status=current_user.status,
        department=current_user.department,
        password_change_required=password_change_required,
    )


@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, current_user: CurrentUser, db: DB):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    return {"success": True}


@router.get("/google/login", response_model=GoogleAuthUrlResponse)
async def google_oauth_login(current_user: CurrentUser):
    _ensure_google_oauth_configured()

    state_token = _create_google_oauth_state(current_user.id)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GOOGLE_OAUTH_SCOPES,
        "state": state_token,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }

    return GoogleAuthUrlResponse(auth_url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback", response_model=GoogleOAuthCallbackResponse)
async def google_oauth_callback(
    code: str,
    state: str,
    db: DB,
):
    _ensure_google_oauth_configured()
    user_id = _decode_google_oauth_state(state)

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for OAuth state")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange Google authorization code",
            )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Google token response missing access token")

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code >= 400:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user profile")

        userinfo_data = userinfo_resp.json()

    expires_in = token_data.get("expires_in")
    user.google_access_token = access_token
    user.google_refresh_token = token_data.get("refresh_token") or user.google_refresh_token
    user.google_token_scope = token_data.get("scope") or settings.GOOGLE_OAUTH_SCOPES
    user.google_email = userinfo_data.get("email")
    user.google_connected_at = datetime.now(timezone.utc)
    if expires_in is not None:
        user.google_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    db.add(AuditLog(
        company_id=user.company_id,
        user_id=user.id,
        action="google_oauth_connected",
        details={"google_email": user.google_email},
    ))
    await db.commit()

    return GoogleOAuthCallbackResponse(
        success=True,
        message="Google account connected successfully",
        google_email=user.google_email,
    )
