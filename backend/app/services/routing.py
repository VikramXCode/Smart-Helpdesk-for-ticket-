"""
services/routing.py – Category → team assignment resolution.

Resolves which team should handle a ticket based on:
1. Company-specific category→team mappings
2. Fallback to default team or None
"""
import uuid
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CompanyTeamMapping, Team

logger = structlog.get_logger(__name__)


async def resolve_team_for_category(
    db: AsyncSession,
    company_id: uuid.UUID,
    category: str,
) -> Optional[str]:
    """
    Look up the team name for a given category in this company's mappings.
    Returns the team name string or None if no mapping exists.
    """
    result = await db.execute(
        select(CompanyTeamMapping).where(
            CompanyTeamMapping.company_id == company_id,
            CompanyTeamMapping.category == category,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        logger.info(
            "team_resolved",
            company_id=str(company_id),
            category=category,
            team=mapping.team_name,
        )
        return mapping.team_name

    # Try case-insensitive match
    result = await db.execute(
        select(CompanyTeamMapping).where(
            CompanyTeamMapping.company_id == company_id,
        )
    )
    all_mappings = result.scalars().all()
    for m in all_mappings:
        if m.category.lower() == category.lower():
            return m.team_name

    logger.info(
        "no_team_mapping",
        company_id=str(company_id),
        category=category,
    )
    return None


async def get_default_team(
    db: AsyncSession,
    company_id: uuid.UUID,
) -> Optional[str]:
    """
    Get the first team for a company as a fallback.
    """
    result = await db.execute(
        select(Team)
        .where(Team.company_id == company_id)
        .limit(1)
    )
    team = result.scalar_one_or_none()
    return team.name if team else None
