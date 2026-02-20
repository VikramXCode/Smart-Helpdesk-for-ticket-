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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import (
    Base,
    Company,
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
        # ── Check if accounts are already seeded ───────────────────────────
        r = await db.execute(select(User).where(User.email == "super@helpdesk.ai"))
        if r.scalar_one_or_none():
            print("✅ Database already seeded — skipping.")
            await engine.dispose()
            return

        print("🌱 Seeding role accounts only…")

        # ── Single tenant company for company-scoped roles ───────────────
        acme = Company(name="Acme Corp", slug="acme", plan_tier="Enterprise", status="active")
        db.add(acme)
        await db.flush()

        # ── Super admin (no company) ───────────────────────────────────────
        super_admin_user = User(
            email="super@helpdesk.ai",
            hashed_password=h("super123"),
            full_name="Super Admin",
            role="super_admin",
            status="online",
            company_id=None,
        )
        db.add(super_admin_user)

        # ── Company-scoped role accounts ─────────────────────────────────
        tom = User(
            company_id=acme.id,
            email="tom@acme.com",
            hashed_password=h("admin123"),
            full_name="Tom Anderson",
            role="company_admin",
            status="online",
            department="IT",
        )
        alex = User(
            company_id=acme.id,
            email="alex@acme.com",
            hashed_password=h("employee123"),
            full_name="Alex Johnson",
            role="employee",
            status="online",
            department="Marketing",
        )
        morgan = User(
            company_id=acme.id,
            email="morgan@acme.com",
            hashed_password=h("staff123"),
            full_name="Alex Morgan",
            role="it_staff",
            status="online",
            department="IT",
        )

        for u in [tom, alex, morgan]:
            db.add(u)
        await db.commit()
        print("✅ Seed complete! Users:")
        print("   super@helpdesk.ai   / super123    (super_admin)")
        print("   tom@acme.com        / admin123    (company_admin)")
        print("   morgan@acme.com     / staff123    (it_staff)")
        print("   alex@acme.com       / employee123 (employee)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
