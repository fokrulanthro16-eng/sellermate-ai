# SellerMate AI — Backend API

A FastAPI backend for Bangladeshi f-commerce merchants. Manages the full commercial lifecycle: products, inventory, orders, customers, analytics, and an AI assistant that understands Bengali.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115.6 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL + asyncpg |
| Cache / Sessions | Redis |
| AI Model | Claude (claude-haiku-4-5-20251001) |
| AI Framework | LangChain / LangGraph |
| Schema Validation | Pydantic v2 |
| Migrations | Alembic |
| Auth | JWT HS256 + Redis refresh tokens |

## Features

- **Multi-tenant** — strict `merchant_id` isolation on every query
- **Order lifecycle** — PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED / CANCELLED / RETURNED with inventory and customer stat automation
- **Analytics** — real-time dashboard, revenue time-series, order breakdown, top products/customers
- **AI assistant** — streaming bilingual (Bengali + English) assistant backed by 5 data tools
- **Strategic agents** — rule-based TrustGraph (merchant reliability 0-100) and FraudSentinel (fraud risk 0-100)
- **WhatsApp webhook** — HMAC-verified inbound handler (processing stub, ready for extension)

## Architecture

```
apps/api/
├── app/
│   ├── ai/
│   │   ├── agent.py                ← Streaming LangGraph agent
│   │   ├── strategic_agents/       ← TrustGraph + FraudSentinel
│   │   ├── prompts/                ← Bengali system prompt
│   │   └── tools/                  ← 5 agent tool modules
│   ├── core/                       ← Config, deps, exceptions
│   ├── db/                         ← Async SQLAlchemy + Redis clients
│   ├── models/                     ← 12 ORM models
│   ├── routers/                    ← 10 FastAPI routers (52 endpoints)
│   ├── schemas/                    ← Pydantic request/response types
│   ├── services/                   ← Business logic layer
│   └── main.py                     ← App factory
├── alembic/                        ← 3 migration revisions
└── tests/                          ← 283 integration tests (all PASS)
```

## Quick Start

See [QUICK_START.md](QUICK_START.md) for full setup instructions.

```bash
# Install
pip install -r requirements.txt

# Migrate
alembic upgrade head

# Run
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` when running.

## API Overview

All routes are prefixed `/api/v1`. JWT required on all routes except `/auth/*` and `/health`.

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| Auth | `/auth` | 8 |
| Merchant | `/merchant` | 5 |
| Products | `/products` | 9 |
| Inventory | `/inventory` | 4 |
| Customers | `/customers` | 8 |
| Orders | `/orders` | 8 |
| Analytics | `/analytics` | 7 |
| AI Assistant | `/assistant` | 5 |
| Hermit Agent | `/ai/hermit` | 3 |
| Strategic Agents | `/ai/strategic` | 4 |

Full endpoint table in [FINAL_MVP_READINESS_REPORT.md](FINAL_MVP_READINESS_REPORT.md).

## Testing

```bash
# Run all 283 tests
python -m pytest tests/ -v

# Run a single module
python -m pytest tests/test_orders.py -v

# Live QA against a running server
python qa_orders.py
```

## Environment Variables

See [QUICK_START.md](QUICK_START.md#environment-variables) for full list.

Minimum required:
```env
ANTHROPIC_API_KEY=sk-ant-...
APP_SECRET_KEY=<change-this>
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sellermate
REDIS_URL=redis://localhost:6379/0
```

## Known Limitations

- No rate limiting on auth endpoints (add before public launch)
- OTP has no attempt counter (brute-force risk)
- WhatsApp inbound processing is a stub
- Plan enforcement not implemented (all merchants get PRO access)
- Windows asyncpg cannot encode pre-1970 timestamps (overview prior-period with wide date ranges)

See [FINAL_MVP_READINESS_REPORT.md](FINAL_MVP_READINESS_REPORT.md) for full production risk assessment.
