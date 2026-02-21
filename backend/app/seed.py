"""
seed.py – Standalone async database seed script.

Seeds only core login accounts (4 roles).
No demo/mock tickets, articles, or analytics data are inserted.

Run with:
    cd backend
    python -m app.seed
"""
import asyncio

from passlib.context import CryptContext
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import (
    Base,
    CompanyTeamMapping,
    Company,
    Team,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def h(password: str) -> str:
    return pwd_context.hash(password)


async def seed():
    if not settings.USE_MOCK_DATA:
        print("⏭️  Skipping seed: USE_MOCK_DATA is false.")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("🌱 Resetting core role accounts and company routing defaults…")

        old_and_new_seed_emails = [
            "super@helpdesk.ai",
            "tom@acme.com",
            "morgan@acme.com",
            "alex@acme.com",
            "platform.super@helpdesk.ai",
            "ava.admin@novaworks.com",
            "liam.staff@novaworks.com",
            "mia.employee@novaworks.com",
        ]

        # Remove previous seed users (old and new) so reseed is deterministic.
        # Use bulk SQL delete to avoid ORM autoflush attempting to null non-null FKs.
        await db.execute(delete(User).where(User.email.in_(old_and_new_seed_emails)))
        await db.flush()

        # Ensure single tenant company for company-scoped roles exists
        company_slug = "novaworks"
        company_result = await db.execute(select(Company).where(Company.slug == company_slug))
        company = company_result.scalar_one_or_none()
        if not company:
            company = Company(
                name="NovaWorks Technologies",
                slug=company_slug,
                plan_tier="Enterprise",
                status="active",
            )
            db.add(company)
            await db.flush()

        # Create/refresh domain teams with rich descriptions for AI-friendly routing context
        team_definitions = {
            "Network": (
                "Handles LAN/WAN connectivity, Wi-Fi issues, VPN access, DNS/DHCP configuration, "
                "firewall and proxy access policies, bandwidth/performance tuning, and outage triage. "
                "Owns incident diagnosis for packet loss, latency spikes, unreachable hosts, and unstable remote access."
            ),
            "Access": (
                "Manages identity and access lifecycle: account provisioning/deprovisioning, password resets, "
                "MFA enrollment/recovery, role/permission changes, SSO access errors, and privileged-access requests. "
                "Ensures least-privilege and compliance-driven entitlement approvals."
            ),
            "Software": (
                "Supports business applications and operating-system software: install/upgrade failures, app crashes, "
                "license activation issues, integration errors, and client-side configuration problems. "
                "Coordinates root-cause analysis for reproducible software defects and patch validation."
            ),
            "Hardware": (
                "Supports physical endpoints and peripherals including laptops, desktops, monitors, docking stations, "
                "printers, scanners, keyboards, and storage devices. Handles diagnostics, component replacement, "
                "device lifecycle, and warranty coordination for hardware faults and performance degradation."
            ),
            "Infrastructure": (
                "Owns core platform and enterprise infrastructure services: servers, virtualization, backup/restore, "
                "storage, database platform availability, cloud/on-prem environment health, and system monitoring. "
                "Leads incident response for service outages, capacity constraints, and recovery operations."
            ),
        }
        teams_by_name = {}
        existing_teams = (
            await db.execute(select(Team).where(Team.company_id == company.id))
        ).scalars().all()

        for team in existing_teams:
            teams_by_name[team.name] = team

        for team_name, team_description in team_definitions.items():
            if team_name not in teams_by_name:
                new_team = Team(
                    company_id=company.id,
                    name=team_name,
                    description=team_description,
                )
                db.add(new_team)
                await db.flush()
                teams_by_name[team_name] = new_team
            else:
                teams_by_name[team_name].description = team_description

        # Replace company mappings so AI category constraints are active immediately
        existing_mappings = (
            await db.execute(select(CompanyTeamMapping).where(CompanyTeamMapping.company_id == company.id))
        ).scalars().all()
        for mapping in existing_mappings:
            await db.delete(mapping)
        await db.flush()

        default_mappings = [
            ("Network", "Network"),
            ("Access", "Access"),
            ("Software", "Software"),
            ("Hardware", "Hardware"),
            ("Infrastructure", "Infrastructure"),
        ]
        for category, team_name in default_mappings:
            db.add(CompanyTeamMapping(company_id=company.id, category=category, team_name=team_name))

        # Super admin (no company)
        super_admin_user = User(
            email="platform.super@helpdesk.ai",
            hashed_password=h("SuperAdmin@123"),
            full_name="Platform Super Admin",
            role="super_admin",
            status="online",
            company_id=None,
        )
        db.add(super_admin_user)

        # Company-scoped role accounts
        company_admin_user = User(
            company_id=company.id,
            email="ava.admin@novaworks.com",
            hashed_password=h("12345678"),
            full_name="Ava Martinez",
            role="company_admin",
            status="online",
            department="IT",
        )
        it_staff_user = User(
            company_id=company.id,
            email="liam.staff@novaworks.com",
            hashed_password=h("ItStaff@123"),
            full_name="Liam Carter",
            role="it_staff",
            status="online",
            department="Network",
            team_id=teams_by_name["Network"].id,
        )
        employee_user = User(
            company_id=company.id,
            email="mia.employee@novaworks.com",
            hashed_password=h("Employee@123"),
            full_name="Mia Reynolds",
            role="employee",
            status="online",
            department="Operations",
        )

        for user in [company_admin_user, it_staff_user, employee_user]:
            db.add(user)

        await db.commit()
        print("✅ Seed complete! Users:")
        print("   platform.super@helpdesk.ai / SuperAdmin@123   (super_admin)")
        print("   ava.admin@novaworks.com    / 12345678         (company_admin, must change on first login)")
        print("   liam.staff@novaworks.com   / ItStaff@123      (it_staff)")
        print("   mia.employee@novaworks.com / Employee@123     (employee)")
        print("✅ Category routing defaults seeded: Network, Access, Software, Hardware, Infrastructure")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
