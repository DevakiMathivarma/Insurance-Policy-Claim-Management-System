# Insurance Policy & Claim Management System

A backend system built with **FastAPI** to run a real insurance company's core
operations — insurance plans, customer policies, beneficiaries, premium
payments, and the full claims lifecycle from submission through document
verification, assessment, approval, and final settlement.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (PostgreSQL also supported) |
| Validation | Pydantic |
| Authentication | JWT (real access + refresh tokens) |
| Migrations | Alembic |
| Caching / Broker | Redis (caching + Celery broker/backend, separate database numbers) |
| Async work | Celery (worker + beat scheduler) |
| PDF generation | ReportLab |
| Excel export | openpyxl |
| Live updates | WebSocket |
| Testing | Pytest |

---

## Features by Level

### ✅ Level 1 – Authentication & User Management
5 roles: Super Admin, Insurance Agent, Claims Officer, Finance Officer, Customer.
Real JWT access + refresh tokens, change-password, account activation/deactivation,
role-based authorization. Super Admin is created automatically on startup and
registers the 3 staff roles directly (flat hierarchy — no sub-hierarchy). Customers
either self-register or are registered by an Insurance Agent on their behalf, both
through the same endpoint.

### ✅ Level 2 – Insurance Plan Management
Full CRUD (Super Admin only), coverage-vs-premium and age-range validation at both
schema and database level, plan-type/status filters, soft delete.

### ✅ Level 3 – Customer Management
Full CRUD, unique email (via the login account) and identification number, age
validation (18+ minimum, checked at registration), hybrid self-service/agent-created
registration through one endpoint.

### ✅ Level 4 – Policy Management
Unique auto-generated policy numbers, plan-eligibility age checking, locked-in
coverage/premium amounts at the moment of purchase, both a direct activation
endpoint and automatic activation on first successful premium payment (both send
the same notification and generate the same policy document).

### ✅ Level 5 – Beneficiary Management
Running-total percentage protection (rejects immediately if an addition would push
the total past 100%, re-checked correctly on updates too), duplicate-beneficiary
prevention.

### ✅ Level 6 – Premium Payment Management
UPI/Card/Net Banking/Auto Debit, duplicate-transaction prevention, exact
amount-matching against the policy's premium, failed payments never activate a
policy, `next_premium_due_date` tracking that powers both overdue detection and
due-reminder notifications.

### ✅ Level 7 – Claim Management
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED → SETTLED lifecycle,
active-policy-only claims, incident-date-within-coverage validation,
claim-amount-vs-coverage validation, duplicate-incident prevention.

### ✅ Level 8 – Claim Document Management
Real file uploads with extension and size validation, document verification
workflow, unverified documents block final claim approval.

### ✅ Level 9 – Claim Assessment
Claims Officer's formal evaluation, eligible amount validated against the policy's
real coverage ceiling, one assessment per claim.

### ✅ Level 10 – Claim Approval & Settlement
Only approved claims can be settled, settlement capped at the assessed eligible
amount, a claim cannot be settled twice, successful settlement flips the claim to
Settled and generates a real PDF settlement letter.

### ✅ Level 11 – Policy Renewal
Eligible-policy checking, new coverage period generated from the old policy's end
date, renewal history traced through `renewed_from_policy_id`, duplicate renewal
prevention.

### ✅ Level 12 – Search, Filtering & Pagination
Implemented across Policies (status, plan type, customer), Claims (status, type,
date range, amount range), and Payments (status, method, date range) — `page`,
`limit`, `sort_by`, `sort_order` throughout.

### ✅ Level 13 – Dashboard & Reports
All 10 summary metrics and all 6 named reports, plus 3 bonus reports (claim type
breakdown, top paying customers, policy status distribution), plus Excel export on
3 of the reports.

### ✅ Level 14 – Notifications
All 8 required notification types, sent through real Celery tasks — policy
activation (with PDF attached), premium payment success, premium due reminder,
claim submission, documents required, claim approval/rejection, claim settlement
(with PDF attached), policy expiry — plus a justified extra (premium overdue
notice).

### ✅ Level 15 – Security & Data Integrity
JWT, role-based authorization, CORS, rate limiting on auth endpoints, global
exception handling, foreign key + unique constraints throughout, soft delete
(Plan), and a real audit log covering every service.

### ✅ Level 16 – Clean Architecture
Full `repositories/` layer built in from day one — every one of the 10 domain
services goes through a dedicated repository for database access, never querying
the database directly in a route or service.

### ✅ Level 17 – Database & Performance
Indexing, `joinedload` used throughout to avoid N+1 queries, SQL-level aggregation
for all dashboard reports rather than pulling rows into Python.

### Bonus Features
- ✅ Redis caching (Customer, Plan, Policy)
- ✅ Celery background workers, including a daily scheduled job for premium due/overdue and policy expiry checks
- ✅ PDF policy document, generated and attached to the activation email
- ✅ PDF claim settlement letter, generated and attached to the settlement email
- ✅ Excel report export (3 reports)
- ✅ Real email via Celery
- ✅ API versioning (`/api/v1/`)
- ✅ WebSocket claim-status notifications (live updates on submit, approve, reject, settle)
- ⬜ Docker & Docker Compose — configuration provided, not yet fully verified running end to end
- ⬜ Pytest unit & integration tests — not yet written for this project

---

## Project Structure

```
app/
├── main.py                  # FastAPI app, routers, startup, exception handlers
├── database.py               # database engine/session
├── config.py                 # centralized environment variable settings
├── celery_app.py             # celery application + broker + beat schedule
├── tasks.py                  # all celery task functions
├── models/                   # 11 SQLAlchemy models
├── schemas/                  # Pydantic request/response schemas
├── repositories/              # database access layer, one per domain table
├── services/                  # business logic, calls repositories
├── routes/                    # FastAPI routers
│   └── websocket.py           # live claim status connection manager
├── auth/                      # current_user, permissions
└── utils/                     # hashing, jwt, pagination, redis_cache, email,
                                # pdf, rate_limit, file_upload, logger

alembic/                       # database migrations
tests/
├── unit/
└── integration/
```

---

## Prerequisites

- Python 3.11 or later
- Redis (Docker: `docker run -d -p 6379:6379 --name redis-insurance redis`)
- SMTP account for real emails (Gmail + App Password works well)

---

## Setup Instructions

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd "Insurance Policy & Claim Management System"

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt<4.1" python-dotenv redis celery alembic reportlab openpyxl python-multipart python-dateutil pytest httpx
```

> **Important:** if `bcrypt` installs as version 4.1 or later, password hashing
> will crash. The pin above (`bcrypt<4.1`) handles this, but double check with
> `pip show bcrypt` if you ever hit login/registration errors.

### 3. Start Redis

```bash
docker run -d -p 6379:6379 --name redis-insurance redis
```

> **If you're also running another project's Docker stack** (this platform was
> built alongside a Property Management and a Travel platform in the same
> environment), make sure only one Redis instance is bound to port 6379 at a
> time — running two projects' Celery stacks against the same Redis will cause
> each project's scheduled tasks to interfere with the other's queue.

### 4. Create your `.env` file

```env
DATABASE_URL=sqlite:///./insurance_platform.db

SECRET_KEY=change-this-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=Admin@12345
DEFAULT_ADMIN_PHONE=9999999999

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60

MAX_UPLOAD_SIZE_MB=10
ALLOWED_UPLOAD_EXTENSIONS=pdf,jpg,jpeg,png
```

### 5. Run database migrations

```bash
alembic init alembic
```

Edit `alembic/env.py` — right after `config = context.config`, add:

```python
import os
import sys
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.database import Base
from app.models import *  # imports and registers all 11 models

config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
target_metadata = Base.metadata
```

**Important:** make sure `app/models/__init__.py` genuinely imports all 11
models — without this, `Base.metadata` has nothing registered, and
`autogenerate` silently produces an empty migration (a real issue we hit and
fixed during development). Also make sure there is only **one**
`target_metadata = ...` line in the whole file — the default Alembic template
also defines `target_metadata = None` further down, which silently overwrites
the real one if both exist.

Clear `sqlalchemy.url` in `alembic.ini` (leave it blank), then:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 6. Start all 3 processes — separate terminals, all running together

**Terminal 1 — the API server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 — the Celery worker (sends every email):**
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

> **Windows-specific note:** the `--pool=solo` flag is required on Windows.
> Celery's default multi-process pool mode is unreliable on Windows and will
> crash with `PermissionError`/`OSError` errors otherwise.

**Terminal 3 — Celery Beat (triggers the daily premium/policy check job):**
```bash
celery -A app.celery_app beat --loglevel=info
```

### 7. Verify it's running

Open `http://localhost:8000/docs`. A default Super Admin is created
automatically — log in with the `DEFAULT_ADMIN_*` credentials from your `.env`.

---

## Running with Docker

```bash
docker-compose up --build
```

Then, in a new terminal, run migrations inside the running app container:
```bash
docker exec -it insurance-app alembic upgrade head
docker-compose restart app
```

> This project's Redis is mapped to host port **6380**, not 6379, specifically
> to avoid colliding with other projects' Docker stacks that may already be
> using the default Redis port.

---

## Real Bugs Found and Fixed During Development

Worth documenting honestly, since these were caught by actually running the
app and carefully re-verifying, not just writing the code once and assuming it
was correct:

1. **The direct `POST /policies/{id}/activate` endpoint was never wired to send
   the activation notification** — a real Celery/PDF wiring pass was done for
   the payment-triggered activation path, but the separate manual activation
   endpoint was missed until a deliberate audit caught the inconsistency. Fixed
   by wiring the same notification logic into both activation paths.
2. **Policy renewal never set `next_premium_due_date` on the new policy** —
   meaning a renewed policy would silently never appear in the daily
   premium-due/overdue checks until its first payment. Fixed by explicitly
   setting this field at renewal time.
3. **An empty Alembic migration was generated** on the first attempt, because
   `app/models/__init__.py` wasn't correctly importing all models before
   `Base.metadata` was read — Alembic found zero tables to create. Fixed by
   verifying and correcting the model registration file directly.
4. **Two different projects' Docker Compose stacks were unintentionally
   sharing the same Redis instance** (both defaulting to port 6379), causing
   one project's scheduled Celery task to be received by another project's
   worker. Resolved by mapping this project's Redis to a distinct host port.

---

