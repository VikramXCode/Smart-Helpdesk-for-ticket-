"""
seed.py – Standalone async database seed script.

Populates the database with demo data matching the frontend mock data exactly.
Idempotent: checks if data exists before inserting.

Run with:
    cd backend
    python -m app.seed
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import (
    Base,
    Company,
    CompanyTeamMapping,
    KnowledgeArticle,
    Team,
    Ticket,
    TicketMessage,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def h(password: str) -> str:
    return pwd_context.hash(password)


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # ── Check if already seeded ────────────────────────────────────────
        r = await db.execute(select(Company).where(Company.slug == "acme"))
        if r.scalar_one_or_none():
            print("✅ Database already seeded — skipping.")
            await engine.dispose()
            return

        print("🌱 Seeding database…")

        # ── Companies ─────────────────────────────────────────────────────
        now = datetime.now(timezone.utc)

        acme = Company(name="Acme Corp", slug="acme", plan_tier="Enterprise", status="active")
        globex = Company(name="Globex Inc", slug="globex", plan_tier="Pro", status="active")
        soylent = Company(name="Soylent Corp", slug="soylent", plan_tier="Basic", status="active")
        initech = Company(name="Initech", slug="initech", plan_tier="Pro", status="active")
        cyberdyne = Company(name="Cyberdyne Systems", slug="cyberdyne", plan_tier="Enterprise", status="active")

        for co in [acme, globex, soylent, initech, cyberdyne]:
            db.add(co)
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

        # ── Acme users ────────────────────────────────────────────────────
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
        sarah = User(
            company_id=acme.id,
            email="sarah@acme.com",
            hashed_password=h("employee123"),
            full_name="Sarah Jenkins",
            role="employee",
            status="away",
            department="Marketing",
        )
        mike = User(
            company_id=acme.id,
            email="mike@acme.com",
            hashed_password=h("staff123"),
            full_name="Mike Ross",
            role="it_staff",
            status="offline",
            department="IT",
        )

        for u in [tom, alex, morgan, sarah, mike]:
            db.add(u)
        await db.flush()

        # ── Globex admin ──────────────────────────────────────────────────
        globex_admin = User(
            company_id=globex.id,
            email="admin@globex.com",
            hashed_password=h("admin123"),
            full_name="Globex Admin",
            role="company_admin",
            status="offline",
        )
        db.add(globex_admin)

        # ── Teams (Acme) ──────────────────────────────────────────────────
        t_it_ops = Team(company_id=acme.id, name="IT Ops", email="it-ops@acme.com")
        t_network = Team(company_id=acme.id, name="Network Team", email="network@acme.com")
        t_hardware = Team(company_id=acme.id, name="Hardware Support", email="hardware@acme.com")
        t_software = Team(company_id=acme.id, name="Software Support", email="software@acme.com")

        for t in [t_it_ops, t_network, t_hardware, t_software]:
            db.add(t)
        await db.flush()

        # Assign staff to teams
        morgan.team_id = t_network.id
        mike.team_id = t_software.id

        # ── Category Mappings (Acme) ───────────────────────────────────────
        for cat, team_name in [
            ("Network", "Network Team"),
            ("Hardware", "Hardware Support"),
            ("Software", "Software Support"),
            ("Access", "IT Ops"),
        ]:
            db.add(CompanyTeamMapping(company_id=acme.id, category=cat, team_name=team_name))

        # ── Tickets ───────────────────────────────────────────────────────
        tickets_data = [
            {
                "ticket_number": "INC-00001",
                "title": "VPN connection failing on macOS",
                "description": "Since the last macOS update I cannot connect to the office VPN. I get error code 619. I've tried reinstalling the VPN client but the issue persists. This is blocking my remote work.",
                "priority": "high",
                "category": "Network",
                "status": "in_progress",
                "assigned_team": "Network Team",
                "source": "web",
                "created_by": alex.id,
                "assigned_to": morgan.id,
                "days_ago": 2,
            },
            {
                "ticket_number": "INC-00002",
                "title": "Request for additional monitor",
                "description": "I would like to request an additional 27-inch monitor for my workstation. I work with multiple applications simultaneously and a second screen would greatly improve my productivity.",
                "priority": "low",
                "category": "Hardware",
                "status": "new",
                "assigned_team": "Hardware Support",
                "source": "web",
                "created_by": sarah.id,
                "assigned_to": None,
                "days_ago": 1,
            },
            {
                "ticket_number": "INC-00003",
                "title": "Password reset for legacy system",
                "description": "I need a password reset for the legacy JIRA system. I have been locked out and cannot access my project boards. This is urgent as I have a deadline tomorrow.",
                "priority": "medium",
                "category": "Access",
                "status": "assigned",
                "assigned_team": "IT Ops",
                "source": "web",
                "created_by": alex.id,
                "assigned_to": mike.id,
                "days_ago": 3,
            },
            {
                "ticket_number": "INC-00004",
                "title": "Software license expiry notification",
                "description": "I received a notification that my Adobe Creative Cloud license expires in 3 days. Please renew it as I use it daily for design work.",
                "priority": "low",
                "category": "Software",
                "status": "new",
                "assigned_team": "Software Support",
                "source": "email",
                "created_by": sarah.id,
                "assigned_to": None,
                "days_ago": 1,
            },
            {
                "ticket_number": "INC-00005",
                "title": "Printer on 3rd floor keeps jamming",
                "description": "The HP LaserJet on the 3rd floor marketing area is constantly jamming. We have tried clearing the paper path but it jams every 5-10 pages.",
                "priority": "medium",
                "category": "Hardware",
                "status": "in_progress",
                "assigned_team": "Hardware Support",
                "source": "web",
                "created_by": alex.id,
                "assigned_to": mike.id,
                "days_ago": 4,
            },
            {
                "ticket_number": "INC-00006",
                "title": "Outlook email sync error",
                "description": "My Outlook is showing a sync error and emails from the last hour are not appearing. Other colleagues on the same Exchange server seem fine.",
                "priority": "high",
                "category": "Software",
                "status": "resolved",
                "assigned_team": "Software Support",
                "source": "web",
                "created_by": sarah.id,
                "assigned_to": morgan.id,
                "days_ago": 5,
                "resolved_days_ago": 4,
            },
        ]

        ticket_objs = []
        for td in tickets_data:
            created = now - timedelta(days=td["days_ago"])
            resolved = None
            if "resolved_days_ago" in td:
                resolved = now - timedelta(days=td["resolved_days_ago"])

            t = Ticket(
                company_id=acme.id,
                ticket_number=td["ticket_number"],
                title=td["title"],
                description=td["description"],
                priority=td["priority"],
                category=td["category"],
                status=td["status"],
                assigned_team=td.get("assigned_team"),
                assigned_to=td.get("assigned_to"),
                created_by=td["created_by"],
                source=td["source"],
                created_at=created,
                updated_at=created,
                resolved_at=resolved,
            )
            db.add(t)
            ticket_objs.append(t)
        await db.flush()

        # Add an initial AI message to the first ticket
        db.add(TicketMessage(
            ticket_id=ticket_objs[0].id,
            author_type="ai",
            content="I've analyzed your VPN issue. This is commonly caused by the Cisco AnyConnect kernel extension being blocked after a macOS security update. Try going to System Preferences → Privacy & Security and allow the Cisco extension. If that doesn't work, reinstall VPN client and re-add the server profile.",
            is_internal=False,
        ))

        # ── Knowledge Articles ────────────────────────────────────────────
        articles_data = [
            {
                "title": "VPN Connection Issues – Troubleshooting Guide",
                "content": """# VPN Connection Issues – Troubleshooting Guide

## Common Causes
VPN connection failures are usually caused by:
- Outdated VPN client software
- Blocked kernel extensions (macOS)
- Firewall rules blocking VPN ports
- Expired certificates

## Step-by-Step Fix

### macOS
1. Open **System Preferences** → **Privacy & Security**
2. Scroll to **Security** section
3. Allow the Cisco Systems or VPN vendor extension
4. Restart your Mac and try connecting again

### Windows
1. Open **Control Panel** → **Network and Sharing Center**
2. Click **Change adapter settings**
3. Right-click your VPN adapter → **Properties**
4. Verify the authentication settings match your IT policy

## Still Not Working?
Submit a ticket with:
- Your OS version
- VPN client version
- Exact error code
- Screenshot of the error""",
                "category": "Network",
                "view_count": 1200,
                "author": morgan,
            },
            {
                "title": "Requesting New Hardware – Process & Guidelines",
                "content": """# Requesting New Hardware

## What Can Be Requested
- Monitors and displays
- Keyboards and mice
- Laptops and workstations
- Headsets and webcams
- Mobile devices

## How to Request
1. Submit a ticket via the portal with category **Hardware**
2. Include the exact make/model if you have a preference
3. Provide a business justification
4. Your manager will receive an approval request

## Timelines
- Standard requests: 5–7 business days
- Urgent requests (with manager approval): 1–2 business days

## Policy Notes
Hardware remains company property. Please do not use company hardware for personal use.""",
                "category": "Hardware",
                "view_count": 850,
                "author": tom,
            },
            {
                "title": "Password Reset Policy & Self-Service Guide",
                "content": """# Password Reset Policy

## Self-Service Reset (Recommended)
1. Go to the login page and click **Forgot Password**
2. Enter your work email address
3. Check your email for a reset link (valid for 15 minutes)
4. Follow the link and set a new password

## Password Requirements
- Minimum 12 characters
- At least one uppercase letter
- At least one number
- At least one special character (!@#$%^&*)
- Cannot reuse last 5 passwords

## Locked Out?
If your account is locked after 5 failed attempts:
- Wait 15 minutes and try again, OR
- Contact IT helpdesk with your employee ID

## Legacy Systems
For JIRA, Confluence, or other legacy systems, submit a ticket with category **Access**.""",
                "category": "Security",
                "view_count": 3400,
                "author": morgan,
            },
            {
                "title": "Slack Integration & Notification Setup Guide",
                "content": """# Slack Integration Guide

## Connecting HelpDesk to Slack
1. Go to **Settings** → **Integrations**
2. Click **Add to Slack**
3. Authorize the HelpDesk AI app in Slack
4. Choose which channel should receive notifications

## Notification Types
You can configure alerts for:
- New ticket created
- Ticket assigned to you
- Ticket status changed
- SLA breach warning

## Slash Commands
Once integrated, use in any Slack channel:
- `/helpdesk create` – Open a ticket
- `/helpdesk status INC-XXXXX` – Check ticket status
- `/helpdesk kb <query>` – Search knowledge base

## Troubleshooting
If the Slack bot doesn't respond, ensure the HelpDesk AI app has been reinstalled after any Slack workspace updates.""",
                "category": "Software",
                "view_count": 620,
                "author": tom,
            },
            {
                "title": "Remote Work Stipend – Eligibility & Reimbursement",
                "content": """# Remote Work Stipend

## Who Is Eligible?
All full-time employees who work remotely at least 3 days per week are eligible for the remote work stipend.

## What's Covered?
- Internet service: up to $50/month
- Home office equipment (one-time): up to $500/year
- Ergonomic accessories: up to $200/year

## How to Claim
1. Submit receipts via the HR portal
2. Use expense category **Remote Work Stipend**
3. Attach itemized receipts
4. Submit by the 15th of each month for same-month reimbursement

## Important Notes
- Reimbursements are processed in the next payroll cycle
- Keep receipts for 12 months
- Personal phone plans are not covered""",
                "category": "HR",
                "view_count": 2100,
                "author": tom,
            },
            {
                "title": "Office Map & Facilities Guide",
                "content": """# Office Map & Facilities

## Floor Layout
- **Ground Floor**: Reception, Meeting Rooms A-D, Cafeteria
- **2nd Floor**: Engineering, Product, Design
- **3rd Floor**: Sales, Marketing, HR
- **4th Floor**: Executive Offices, Large Conference Room

## Meeting Room Booking
Reserve rooms via the Google Calendar integration:
1. Create a calendar event
2. Click **Add rooms**
3. Search for the room by name or floor
4. Rooms auto-release if not checked in within 10 minutes

## Facilities
- **Gym**: Ground floor, open 7am–9pm, badge access required
- **Cafeteria**: 7:30am–2:30pm, subsidized meals
- **Bike parking**: Underground, request access from reception
- **Lockers**: Available on each floor, request key from reception

## Visitor Access
All visitors must register at reception and will receive a temporary badge.""",
                "category": "General",
                "view_count": 450,
                "author": tom,
            },
        ]

        for ad in articles_data:
            article = KnowledgeArticle(
                company_id=acme.id,
                title=ad["title"],
                content=ad["content"],
                category=ad["category"],
                view_count=ad["view_count"],
                author_id=ad["author"].id,
            )
            db.add(article)

        await db.commit()
        print("✅ Seed complete! Users:")
        print("   super@helpdesk.ai   / super123    (super_admin)")
        print("   tom@acme.com        / admin123    (company_admin)")
        print("   morgan@acme.com     / staff123    (it_staff)")
        print("   alex@acme.com       / employee123 (employee)")
        print("   sarah@acme.com      / employee123 (employee)")
        print("   mike@acme.com       / staff123    (it_staff)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
