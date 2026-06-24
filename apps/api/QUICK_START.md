# SellerMate AI — Quick Start Guide

This guide gets the backend running locally from scratch.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | 3.14 tested |
| PostgreSQL | 13+ | Local or Docker |
| Redis | 6+ | Local or Docker |
| Git | Any | |

---

## Step 1 — Clone and Install

```bash
git clone <repo-url>
cd sellermate/apps/api

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Mac / Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2 — PostgreSQL Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE sellermate;
CREATE USER sellermate_user WITH PASSWORD 'sellermate_pass';
GRANT ALL PRIVILEGES ON DATABASE sellermate TO sellermate_user;
\q
```

Or using Docker:
```bash
docker run -d \
  --name sellermate-pg \
  -e POSTGRES_DB=sellermate \
  -e POSTGRES_USER=sellermate_user \
  -e POSTGRES_PASSWORD=sellermate_pass \
  -p 5432:5432 \
  postgres:15
```

---

## Step 3 — Redis Setup

```bash
# Local Redis (if installed)
redis-server

# Or with Docker
docker run -d \
  --name sellermate-redis \
  -p 6379:6379 \
  redis:7
```

---

## Step 4 — Environment Variables

Create `apps/api/.env`:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...
APP_SECRET_KEY=change-me-use-a-64-char-random-hex-string

# Database
DATABASE_URL=postgresql+asyncpg://sellermate_user:sellermate_pass@localhost:5432/sellermate

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3 / Cloudflare R2 (for image uploads)
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET_NAME=sellermate-uploads
S3_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com  # omit for AWS S3

# WhatsApp Cloud API (optional — stub available without these)
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=any-string-you-choose
WHATSAPP_APP_SECRET=

# App settings
APP_ENV=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 5 — Run Database Migrations

```bash
cd apps/api
alembic upgrade head
```

Verify tables were created:
```bash
psql -U sellermate_user -d sellermate -c "\dt"
```

Expected output:
```
 conversations
 customers
 hermit_insights
 inventory_logs
 merchants
 messages
 order_items
 order_status_history
 orders
 product_variants
 products
 strategic_insights
```

---

## Step 6 — Start the Server

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables hot-reload during development.

Visit:
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

---

## Step 7 — Verify Everything Works

```bash
# Health check
curl http://localhost:8000/health

# Register a merchant
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone": "+8801700000001",
    "password": "TestPass123!",
    "business_name": "My Test Shop",
    "owner_name": "Test Owner",
    "business_type": "FASHION_CLOTHING"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "+8801700000001", "password": "TestPass123!"}'
```

Save the `access_token` from the login response — all subsequent requests need it in the header:
```
Authorization: Bearer <access_token>
```

---

## Step 8 — Run Tests

```bash
# Set up test database
psql -U postgres -c "CREATE DATABASE sellermate_test;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sellermate_test TO sellermate_user;"

# Set test DATABASE_URL (add to .env or set inline)
export TEST_DATABASE_URL=postgresql+asyncpg://sellermate_user:sellermate_pass@localhost:5432/sellermate_test

# Run all 283 tests
python -m pytest tests/ -v

# Run a specific test module
python -m pytest tests/test_orders.py -v

# Run with output (shows print statements)
python -m pytest tests/ -s
```

---

## Docker Compose (All-in-One)

Create `docker-compose.yml` in the project root:

```yaml
version: "3.9"
services:
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    env_file:
      - ./apps/api/.env
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sellermate
      POSTGRES_USER: sellermate_user
      POSTGRES_PASSWORD: sellermate_pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

```bash
docker-compose up -d
docker-compose exec api alembic upgrade head
```

---

## Common Issues

**`asyncpg.InvalidPasswordError`**  
Check `DATABASE_URL` credentials match the PostgreSQL user/password you created.

**`redis.exceptions.ConnectionError`**  
Make sure Redis is running: `redis-cli ping` should return `PONG`.

**`ANTHROPIC_API_KEY not configured`**  
The AI assistant endpoints will fail without a valid Anthropic API key. The rest of the API works without it.

**`alembic.util.exc.CommandError: Can't locate revision`**  
Run from the `apps/api` directory, not the repo root.

**Pre-1970 timestamp error on Windows**  
Do not use date ranges in analytics that produce a prior period before 1970-01-01 on Windows. Use bounded ranges like `from_date=2024-01-01&to_date=2026-12-31`.

**Tests fail with "relation does not exist"**  
The test database tables are missing. Run `alembic upgrade head` against your test database, or let `conftest.py` recreate them via `create_all`.
