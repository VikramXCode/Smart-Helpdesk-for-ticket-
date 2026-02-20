"""
routes/auth.py – Authentication endpoints.
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, verify_password
from app.dependencies import CurrentUser, DB, get_db
from app.models import AuditLog, Company, User
from app.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


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
    )

    return TokenResponse(access_token=token, user=user_out)


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
    )
