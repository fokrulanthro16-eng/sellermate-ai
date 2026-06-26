# SellerMate AI

> **⚠️ PUBLIC BETA — v0.9-beta**
>
> This is a pre-release build for testing and feedback only. Not for production use.
>
> | What is mocked in beta | Details |
> |---|---|
> | 💳 Payments | No real charges — bKash, Nagad, SSLCommerz all simulate success |
> | 🚚 Courier booking | No real parcels — Pathao, Steadfast, REDX return fake tracking IDs |
> | 📱 OTP / SMS | OTP printed to backend console, not sent to your phone |
> | 🤖 AI content | Works without API keys — uses rule-based fallback automatically |
> | 🖼️ Image uploads | Base64 local storage — configure S3/R2 for persistence |
>
> **No real money moves. No real courier bookings. Safe to test freely.**

---

**AI-powered Commerce OS for Bangladeshi e-commerce sellers.**

SellerMate AI gives small online sellers a single dashboard to run their entire business — orders, inventory, customers, analytics, AI content, and a public storefront — without needing multiple tools or technical expertise.

---

## What It Does

| Module | What it gives you |
|---|---|
| **Orders** | Manage orders across channels, update status, collect COD |
| **Products** | Add, edit, and categorise your product catalogue |
| **Inventory** | Track stock, get low-stock alerts, log adjustments |
| **Customers** | Customer profiles, order history, VIP tagging |
| **Analytics** | Revenue, order breakdown, top products — 7/30/90 day views |
| **Store Builder** | Customise your public storefront with logo, banner, description |
| **Marketplace** | Public-facing marketplace listing your store |
| **Public Store** | Buyer-facing store page at `/store/<your-slug>` |
| **Cart & Checkout** | Full buyer checkout with COD and payment gateway support |
| **AI Tools** | Generate Facebook posts, captions, hashtags, product descriptions |
| **AI Agents** | Automated business analysis: sales trends, inventory health, trust score |
| **Courier Integration** | Book shipments with Pathao, Steadfast, REDX (mock in beta) |
| **Payment Integration** | bKash, Nagad, SSLCommerz (mock in beta) |

---

## Current Beta Features

- Full seller dashboard with KPI cards and daily action suggestions
- Order management with status workflow
- Product and inventory management
- Customer management with segments
- Public store with product catalogue, search, and category filters
- Buyer cart and checkout (COD + mock payment)
- Order tracking page
- AI-generated marketing content (with or without real AI API keys)
- AI agents for business intelligence
- Bangla / English bilingual UI (toggle in sidebar)
- Demo account pre-loaded with 90+ products, 50+ orders, 20+ customers

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2 (async), Alembic |
| Frontend | Next.js 15 (App Router), React 19, TypeScript |
| Database | PostgreSQL 13+ |
| Cache / Queue | Redis 7+ |
| AI | Gemini / Claude / OpenAI (falls back to rule-based templates) |
| Styling | Tailwind CSS |
| State | TanStack Query v5 |
| Monorepo | Turborepo |

---

## Folder Structure

```
sellermate/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── ai/             # AI agents, commerce engine
│   │   │   ├── core/           # Config, auth, database, exceptions
│   │   │   ├── integrations/   # Courier, payment, marketplace clients
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   ├── routers/        # API route handlers
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   └── services/       # Business logic services
│   │   ├── alembic/            # Database migration scripts
│   │   ├── scripts/            # seed_demo.py, seed_beta.py
│   │   ├── .env.example        # Environment variable template
│   │   ├── .env.production.example
│   │   └── requirements.txt
│   └── web/                    # Next.js 15 frontend
│       ├── src/
│       │   ├── app/
│       │   │   ├── (auth)/     # Login, register, onboarding
│       │   │   ├── (dashboard)/# Seller dashboard pages
│       │   │   └── (public)/   # Marketplace, store, cart, checkout
│       │   ├── components/     # Shared UI components
│       │   ├── hooks/          # TanStack Query hooks
│       │   ├── lib/            # API client, auth, utilities
│       │   └── types/          # TypeScript types
│       └── .env.local.example
├── docker-compose.yml          # PostgreSQL + Redis (infrastructure only)
├── docker-compose.prod.yml     # Full production stack
├── BETA_NOTES.md               # What is mocked / what is real
├── TESTING_GUIDE.md            # Step-by-step test flows
├── FEEDBACK_TEMPLATE.md        # Template for bug reports
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 / 3.14 tested |
| Node.js | 18+ | 20 LTS recommended |
| npm | 9+ | Included with Node |
| PostgreSQL | 13+ | Or run via Docker (see below) |
| Redis | 6+ | Or run via Docker (see below) |
| Git | Any | |

---

## Local Setup — Step by Step

### Option A: Infrastructure via Docker, apps manually (recommended for testers)

Start PostgreSQL and Redis with one command:

```bash
docker-compose up -d postgres redis
```

Then follow the backend and frontend setup below.

### Option B: Full manual setup (PostgreSQL and Redis installed locally)

Skip the docker-compose step and make sure PostgreSQL and Redis are running locally.

---

## Backend Setup

```bash
# 1. Enter the API directory
cd apps/api

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file
cp .env.example .env
```

Edit `apps/api/.env` — at minimum set these three values:

```env
APP_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=postgresql+asyncpg://sellermate:password@localhost:5432/sellermate
REDIS_URL=redis://localhost:6379/0
```

> All other variables are optional for local testing. Courier, payment, AI, and S3 integrations fall back to mock/local mode when credentials are not set.

```bash
# 5. Run database migrations
alembic upgrade head

# 6. Seed the demo account and beta data
python scripts/seed_demo.py
python scripts/seed_beta.py

# 7. Start the backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Mac / Linux:
# python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at `http://localhost:8000`.
Health check: `http://localhost:8000/api/v1/health`

---

## Frontend Setup

```bash
# In a new terminal
cd apps/web

# 1. Create your environment file
cp .env.local.example .env.local

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev
```

The frontend is now running at `http://localhost:3000`.

---

## Environment Variables

### Backend (`apps/api/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_SECRET_KEY` | Yes | — | 64-char hex for JWT signing |
| `DATABASE_URL` | Yes | — | PostgreSQL async connection URL |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL |
| `APP_ENV` | No | `development` | `development` or `production` |
| `GEMINI_API_KEY` | No | — | Enables Google Gemini AI |
| `ANTHROPIC_API_KEY` | No | — | Enables Claude AI |
| `OPENAI_API_KEY` | No | — | Enables OpenAI |
| `S3_ACCESS_KEY` | No | — | Cloudflare R2 / AWS S3 |
| `PATHAO_CLIENT_ID` | No | — | Pathao courier (mock if empty) |
| `STEADFAST_API_KEY` | No | — | Steadfast courier (mock if empty) |
| `BKASH_APP_KEY` | No | — | bKash payment (mock if empty) |
| `SSLCOMMERZ_STORE_ID` | No | — | SSLCommerz (mock if empty) |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | CORS allowed origins |

See `apps/api/.env.example` for the complete list.

### Frontend (`apps/web/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000/api/v1` | Backend API base URL |

---

## Demo Login Credentials

```
Email:    demo@sellermate.ai
Password: Demo1234!
Phone:    +8801700000001
```

Or click **"ডেমো হিসেবে ঢুকুন"** on the login / register page — this button logs in automatically.

Demo store public URL: `http://localhost:3000/store/demo-shop`

---

## Testing Checklist

Work through each of these to verify a working install:

- [ ] `http://localhost:8000/api/v1/health` returns `{"status":"ok"}`
- [ ] `http://localhost:3000` redirects to `/dashboard` (after login)
- [ ] Demo login button on `/login` enters the dashboard
- [ ] Dashboard KPI cards load (orders, revenue, stock)
- [ ] `/marketplace` shows the Demo Shop card
- [ ] `/store/demo-shop` loads 90+ products
- [ ] Add a product to cart → cart count increases
- [ ] Checkout form → submit → order number shown
- [ ] `/track-order` → enter order number → tracking displayed
- [ ] `/store-builder` loads the store settings form (not stuck)
- [ ] `/ai-tools` → generate content → copy works
- [ ] `/agents` → run an agent → results shown

Full test flows: see [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## Known Limitations (Beta)

- **Payments are mocked** — no real money movement. See [BETA_NOTES.md](BETA_NOTES.md).
- **Courier bookings are mocked** — fake tracking IDs generated locally.
- **OTP delivery is mocked** — OTP is printed to the backend console, not sent by SMS.
- **File uploads are base64 local** — configure S3/R2 for persistent image hosting.
- **AI is optional** — works without any AI API key using rule-based fallback.
- **Single-tenant** — each install is single-merchant. Multi-merchant is on the roadmap.
- **No mobile app yet** — web only.

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 1-4 | Core backend, auth, products, orders, inventory, customers | Done |
| Phase 5 | Integration layer (courier, payment, marketplace connectors) | Done |
| Phase 6 | Production foundation (migrations, config, healthcheck) | Done |
| Phase 7 | Connector readiness (webhook handlers, mock clients) | Done |
| Phase 8 | Public storefront and buyer checkout | Done |
| Phase 9 | AI tools and seller intelligence | Done |
| Phase 10 | Trust and safety engine | Done |
| Phase 11 | Beta UI, demo mode, public buyer pages | Done |
| **Beta** | **Public beta testing** | **Now** |
| Phase 12 | Multi-tenant, mobile app, real courier/payment live mode | Upcoming |

---

## How Testers Should Give Feedback

1. Work through [TESTING_GUIDE.md](TESTING_GUIDE.md)
2. Fill in [FEEDBACK_TEMPLATE.md](FEEDBACK_TEMPLATE.md) for each issue
3. Send to **fokrulanthro16@gmail.com** with subject: `[SellerMate Beta] Feedback — <your name>`
4. Or open a GitHub Issue with the label `beta-feedback`

Please include: what page, what steps, what you expected, what happened, and a screenshot if possible.

---

## License

Private beta. Not for redistribution.
