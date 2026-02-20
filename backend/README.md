# HelpDesk AI — Backend

FastAPI + PostgreSQL (pgvector) + Celery + Redis backend for the HelpDesk AI SaaS platform.

---

## Requirements

- Python 3.11+
- PostgreSQL 15+ with the `pgvector` extension enabled (e.g. [Neon](https://neon.tech))
- Redis (local or [Upstash](https://upstash.com))
- Docker + Docker Compose (optional, for containerised setup)

---

## Quick Start (local)

### 1. Clone & create a virtual environment

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in at minimum:
#   DATABASE_URL  — Postgres connection string (asyncpg driver)
#   SECRET_KEY    — random hex string (openssl rand -hex 32)
# All other keys are optional; the app falls back to mock responses.
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Seed demo data

Populates companies, users, tickets, knowledge articles, and analytics fixtures
so the frontend demo works out of the box.

```bash
python -m app.seed
```

**Demo accounts created by seed:**

| Email | Password | Role |
|---|---|---|
| `super@helpdesk.ai` | `super123` | Super Admin |
| `tom@acme.com` | `admin123` | Company Admin (Acme Corp) |
| `alex@acme.com` | `employee123` | Employee (Acme Corp) |
| `morgan@acme.com` | `staff123` | IT Staff (Acme Corp) |
| `sarah@acme.com` | `employee123` | Employee (Acme Corp) |
| `mike@acme.com` | `staff123` | IT Staff (Acme Corp) |

### 6. Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 7. Start the Celery worker (optional)

Required only for background AI processing tasks (ticket routing, trend detection).

```bash
celery -A app.celery_app worker --loglevel=info
```

---

## Docker Compose

Starts the API, Celery worker, and a local PostgreSQL + Redis instance.

```bash
# from the backend/ directory
docker compose up --build
```

Services:
| Service | Port |
|---|---|
| FastAPI | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

To seed the database after containers are up:

```bash
docker compose exec api python -m app.seed
```

---

## Environment Variables

See `.env.example` for the full list with descriptions.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | asyncpg connection string |
| `SECRET_KEY` | Yes | JWT signing secret |
| `REDIS_URL` | No | Celery broker (defaults to `redis://localhost:6379/0`) |
| `GROQ_API_KEY` | No | LLM for AI summarisation (mocked if absent) |
| `JINA_API_KEY` | No | Embeddings for vector search (mocked if absent) |
| `RESEND_API_KEY` | No | Email notifications (mocked if absent) |
| `TWILIO_*` | No | SMS notifications (mocked if absent) |
| `SENTRY_DSN` | No | Error tracking |

---

## Project Structure

```
backend/
├── alembic/                  # Database migrations
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
├── app/
│   ├── main.py               # FastAPI app factory, CORS, router registration
│   ├── config.py             # Pydantic settings (reads .env)
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── dependencies.py       # Auth dependencies (CurrentUser, DB, role guards)
│   ├── seed.py               # Demo data seeder
│   ├── celery_app.py         # Celery instance
│   ├── auth/
│   │   └── jwt.py            # Token creation & verification
│   ├── routes/
│   │   ├── auth.py           # POST /auth/login, GET /auth/me
│   │   ├── tickets.py        # CRUD + messages + resolve
│   │   ├── knowledge.py      # GET /knowledge/
│   │   ├── analytics.py      # GET /analytics/overview|volume|categories
│   │   ├── admin.py          # GET/POST /admin/agents|teams|mappings
│   │   ├── super_admin.py    # GET/POST /super-admin/stats|companies
│   │   ├── chat.py           # POST /chat/
│   │   └── webhooks.py       # POST /webhooks/
│   ├── services/
│   │   ├── ai.py             # Groq LLM calls
│   │   ├── vector.py         # Jina embeddings + pgvector search
│   │   ├── notifications.py  # Resend email + Twilio SMS
│   │   └── routing.py        # Auto-assign tickets to teams
│   ├── tasks/
│   │   ├── ticket_processing.py  # Celery task: AI summary + routing
│   │   └── trend_detection.py    # Celery task: cluster similar tickets
│   └── utils/
│       ├── logging.py        # structlog setup
│       └── exceptions.py     # HTTP exception helpers
├── alembic.ini
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## API Reference

All endpoints are prefixed with `/api/v1/`.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | — | Email + password → JWT |
| GET | `/auth/me` | Any | Current user info |
| GET | `/tickets/` | IT Staff+ | List / search tickets |
| POST | `/tickets/` | Employee+ | Submit new ticket |
| GET | `/tickets/:id` | IT Staff+ | Ticket detail + messages |
| PATCH | `/tickets/:id` | IT Staff+ | Update status / priority |
| POST | `/tickets/:id/resolve` | IT Staff+ | Mark resolved |
| POST | `/tickets/:id/messages` | Any | Add message / reply |
| GET | `/knowledge/` | Any | Search knowledge articles |
| GET | `/analytics/overview` | Company Admin+ | KPI summary |
| GET | `/analytics/volume` | Company Admin+ | Ticket volume over time |
| GET | `/analytics/categories` | Company Admin+ | Breakdown by category |
| GET | `/admin/agents` | Company Admin | List agents |
| POST | `/admin/agents` | Company Admin | Invite new agent |
| GET | `/admin/teams` | Company Admin | List teams |
| GET | `/admin/mappings` | Company Admin | Team–category mappings |
| GET | `/super-admin/stats` | Super Admin | Platform-wide KPIs |
| GET | `/super-admin/companies` | Super Admin | List all companies |
| POST | `/super-admin/companies` | Super Admin | Onboard new company |
| POST | `/chat/` | Any | AI chat assistant |

Full interactive documentation is available at `/docs` (Swagger UI) and `/redoc`.
