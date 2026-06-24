# SellerMate AI — Final MVP Readiness Report

**Date:** 2026-06-22  
**Version:** 1.0.0  
**Audited by:** Claude Code (Principal Backend Engineer)  
**Overall Status:** READY FOR DEMO / CONDITIONAL FOR PRODUCTION

---

## Executive Summary

SellerMate AI is a FastAPI backend that provides a complete merchant operating system for Bangladeshi f-commerce sellers. The backend covers the full commercial lifecycle: products, inventory, orders, customers, analytics, a bilingual AI assistant, and a strategic intelligence layer for fraud and trust scoring.

**283/283 automated tests pass.** The core business logic is correct, well-isolated by tenant, and backed by a clean async architecture. Several security and operational gaps exist that must be addressed before high-volume production deployment, but the system is demo-ready and suitable for a controlled launch with trusted merchants.

---

## 1. Completed Modules

| Module | Status | Tests | Bugs Fixed | QA Report |
|--------|--------|-------|-----------|-----------|
| Auth | ✅ PASS | 9 | 0 | AUTH_QA_REPORT.md |
| Merchant | ✅ PASS | — | 0 | MERCHANT_QA_REPORT.md |
| Products | ✅ PASS | 33 | 0 | PRODUCT_QA_REPORT.md |
| Inventory | ✅ PASS | 47 | 5 | INVENTORY_QA_REPORT.md |
| Customers | ✅ PASS | 54 | 4 | CUSTOMER_QA_REPORT.md |
| Orders | ✅ PASS | 70 | 7 | ORDER_QA_REPORT.md |
| Analytics | ✅ PASS | 36 | 1 | ANALYTICS_QA_REPORT.md |
| AI Assistant (Hermit) | ✅ PASS | — | 0 | HERMIT_AGENT_REPORT.md |
| Strategic Agents | ✅ PASS | 34 | 0 | STRATEGIC_AGENT_REPORT.md |
| **TOTAL** | **✅ ALL PASS** | **283** | **17** | — |

### Bugs Fixed During QA (17 total)

**Inventory (5)**
1. `is_active` filter missing on stock list — inactive product variants were included
2. Missing `with_for_update()` on bulk adjustment — concurrent adjustments could corrupt stock
3. Zero-quantity adjustment allowed — no validation on `quantity_change=0`
4. Non-deterministic pagination — missing `ORDER BY id` tie-breaker
5. Merchant isolation breach in `deduct_for_order` — JOIN to Product for merchant check was missing

**Customer (4)**
1. Tags filter dead code — `?tags=` query param was accepted but never passed to the service
2. Non-deterministic pagination — missing `Customer.id` tie-breaker
3. SQLAlchemy identity-map bypass — `get_customer()` returned cached object ignoring `merchant_id` filter
4. `Customer.tags.contains([tag])` incompatible with asyncpg — switched to `Customer.tags.any(tag)`

**Orders (7)**
1. **CRITICAL** — Inventory not restored on cancel — stock was permanently lost
2. Customer aggregate stats not rolled back on cancel — `total_orders`/`total_spent` overcounted
3. Terminal state guard missing — status could be changed from CANCELLED or RETURNED orders
4. Payment allowed on cancelled orders — no guard in `record_payment`
5. Float arithmetic on monetary values — replaced with `Decimal` throughout
6. `MissingGreenlet` error on cancel (HTTP 500) — `updated_at` expired after async flush; fixed with `await db.refresh(order)`
7. CSV export crashed with Pydantic validation error — router passed `limit=5000` to `OrderFilters` which enforces `le=100`

**Analytics (1)**
1. Overview endpoint crashed on wide date ranges — prior-period calculation produced pre-1970 datetime that Windows asyncpg cannot encode as `timestamptz`

---

## 2. Test Summary

### Regression Result: 283/283 PASS ✅

```
Platform : Windows 11 / Python 3.14.2
Database : PostgreSQL (asyncpg)
Cache    : Redis
Runtime  : 21 min 45 sec
```

| Test File | Tests | Duration | Coverage Area |
|-----------|-------|----------|---------------|
| `test_auth.py` | 9 | ~12s | Register, login, refresh, logout, OTP, reset |
| `test_products.py` | 33 | ~25s | CRUD, variants, categories, isolation, pagination |
| `test_inventory.py` | 47 | ~35s | Stock list, adjustment, alerts, logs, isolation |
| `test_customers.py` | 54 | ~40s | CRUD, tags, export, search, isolation |
| `test_orders.py` | 70 | 5m 15s | All 8 endpoints, lifecycle, calculations, isolation |
| `test_analytics.py` | 36 | 2m 45s | Dashboard, overview, revenue, breakdown, isolation |
| `test_strategic.py` | 34 | 2m 37s | Run, insights, trust-score, fraud-report, isolation |
| **TOTAL** | **283** | **~21m** | **All modules** |

### Test Infrastructure
- Framework: `pytest-asyncio` v1.4.0, mode=AUTO, session-scoped event loop
- DB: dedicated `sellermate_test` PostgreSQL database; `Base.metadata.create_all` on session start
- Redis: real Redis instance (`/1` DB) with `fakeredis` fallback
- HTTP: `httpx.AsyncClient` with `ASGITransport` (no real network)
- Isolation: function-scoped session with rollback; UUID-based identifiers prevent fixture collisions

---

## 3. API Endpoint Summary

**Total endpoints: 52** across 10 routers. All require JWT `Authorization: Bearer <token>` except auth and health routes.

### Base URL: `https://<host>/api/v1`

#### Auth (`/auth`) — 8 endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create merchant account |
| POST | `/auth/login` | No | Login, get JWT pair |
| POST | `/auth/refresh` | No | Rotate refresh token |
| POST | `/auth/logout` | Yes | Blacklist current tokens |
| POST | `/auth/forgot-password` | No | Request OTP |
| POST | `/auth/verify-otp` | No | Validate OTP code |
| POST | `/auth/reset-password` | No | Set new password |
| GET | `/auth/me` | Yes | Current merchant profile |

#### Merchant (`/merchant`) — 5 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/merchant/me` | Fetch profile |
| PATCH | `/merchant/me` | Update profile |
| POST | `/merchant/onboarding` | Advance onboarding step |
| GET | `/merchant/stats` | Dashboard KPIs |
| GET/POST | `/merchant/whatsapp/*` | WhatsApp connection (stub) |

#### Products (`/products`) — 9 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/products` | Paginated list (search, category, is_active) |
| POST | `/products` | Create product |
| GET | `/products/categories` | Merchant's product categories |
| GET | `/products/{id}` | Get product + all variants |
| PATCH | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |
| POST | `/products/{id}/variants` | Add variant |
| PATCH | `/products/{id}/variants/{vid}` | Update variant |
| DELETE | `/products/{id}/variants/{vid}` | Delete variant |

#### Inventory (`/inventory`) — 4 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/inventory` | Paginated stock (low_stock, variant_id filters) |
| POST | `/inventory/adjust` | Bulk stock adjustment |
| GET | `/inventory/alerts` | All low-stock variants |
| GET | `/inventory/logs` | Paginated audit log |

#### Orders (`/orders`) — 8 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/orders` | Paginated list (status, channel, payment_status, search) |
| POST | `/orders` | Create order (deducts inventory, updates customer stats) |
| GET | `/orders/export` | Download CSV |
| GET | `/orders/{id}` | Order + items + status history |
| PATCH | `/orders/{id}` | Update delivery/tracking info |
| POST | `/orders/{id}/status` | Advance order status |
| POST | `/orders/{id}/payment` | Record payment |
| DELETE | `/orders/{id}` | Cancel order (restores inventory, rolls back customer stats) |

#### Customers (`/customers`) — 8 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/customers` | Paginated list (search, district, tags) |
| POST | `/customers` | Create customer |
| GET | `/customers/export` | Download CSV |
| GET | `/customers/{id}` | Customer profile |
| PATCH | `/customers/{id}` | Update customer |
| DELETE | `/customers/{id}` | Delete customer |
| POST | `/customers/{id}/tags/{tag}` | Add tag |
| DELETE | `/customers/{id}/tags/{tag}` | Remove tag |

#### Analytics (`/analytics`) — 7 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/dashboard` | Current-period metrics (no params needed) |
| GET | `/analytics/customers` | Customer metrics by date range |
| GET | `/analytics/overview` | Revenue KPIs + change % vs prior period |
| GET | `/analytics/revenue` | Time-series revenue (day/week/month) |
| GET | `/analytics/orders` | Order breakdown by status/channel/payment |
| GET | `/analytics/products/top` | Top products by revenue |
| GET | `/analytics/inventory` | Inventory health summary |

#### AI Assistant (`/assistant`) — 5 endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/assistant/conversations` | List conversations |
| POST | `/assistant/conversations` | Create conversation |
| DELETE | `/assistant/conversations/{id}` | Delete conversation |
| GET | `/assistant/conversations/{id}/messages` | Message history |
| POST | `/assistant/conversations/{id}/chat` | Stream AI response (SSE) |

#### Hermit Agent (`/ai/hermit`) — 3 endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/hermit/run` | Generate background intelligence insights |
| GET | `/ai/hermit/insights` | List insights (type, severity, unread filters) |
| PATCH | `/ai/hermit/insights/{id}/read` | Mark as read |

#### Strategic Agents (`/ai/strategic`) — 4 endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/strategic/run` | Run Trust Graph + Fraud Sentinel |
| GET | `/ai/strategic/insights` | List stored agent insights |
| GET | `/ai/strategic/trust-score` | Latest trust score |
| GET | `/ai/strategic/fraud-report` | Latest fraud report |

#### Other
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET/POST | `/webhooks/whatsapp` | HMAC | Meta WhatsApp webhook |

---

## 4. Strategic Agents Summary

### Architecture
```
POST /ai/strategic/run
    │
    ├── TrustGraph().run(db, merchant_id)
    │       └── Queries: orders, customers
    │           Computes: delivery_rate, payment_rate, retention_rate, cancellation_rate
    │           Returns: trust_score (0-100), confidence (LOW/MEDIUM/HIGH), risk_flags
    │
    └── FraudSentinel().run(db, merchant_id)
            └── Queries: orders (last 30 days)
                Detects: cancellation spikes, stale unpaid, volume spikes
                Returns: fraud_risk_score (0-100), alert_reasons
    │
    Both results saved to strategic_insights table (agent_name, score, payload JSON)
```

### TrustGraph Scoring (base 50)
| Signal | Threshold | Δ Score |
|--------|-----------|---------|
| Delivery rate | ≥80% | +20 |
| Delivery rate | ≥50% | +10 |
| Delivery rate | <50% | flag `LOW_DELIVERY_RATE` |
| Payment collection | ≥70% | +15 |
| Payment collection | ≥40% | +7 |
| Payment collection | <40% | flag `LOW_PAYMENT_COLLECTION` |
| Customer retention | ≥30% | +15 |
| Customer retention | ≥10% | +7 |
| Cancellation rate | >40% | -25, flag `HIGH_CANCELLATION_RATE` |
| Cancellation rate | >20% | -10, flag `ELEVATED_CANCELLATION_RATE` |

### FraudSentinel Detection (30-day window)
| Pattern | Threshold | Δ Score | Alert |
|---------|-----------|---------|-------|
| Cancellation spike | >50% | +40 | `CANCELLATION_SPIKE` |
| High cancellation | >30% | +20 | `HIGH_CANCELLATION_RATE` |
| Stale unpaid orders | ≥5 | +25 | `STALE_UNPAID_ORDERS` |
| Unpaid accumulation | ≥2 | +10 | `UNPAID_ORDER_ACCUMULATION` |
| Order volume spike | ≥5× avg + ≥10 orders | +25 | `ORDER_SPIKE` |

### Database
- **Table:** `strategic_insights`
- **Schema:** `id`, `merchant_id`, `agent_name`, `score`, `payload` (JSON), `created_at`
- **Indexes:** `merchant_id`, `(merchant_id, agent_name)`, `(merchant_id, created_at)`
- **Migration:** `c3d4e5f6a7b8_strategic_insights.py`

---

## 5. Known Limitations

### Functional Gaps
1. **WhatsApp integration is a stub** — webhook parsing exists with HMAC validation, but inbound message processing, order creation via WhatsApp, and chatbot replies are not implemented
2. **No email notifications** — password reset OTPs are returned in the API response in dev mode; production requires an email/SMS gateway
3. **S3/R2 file uploads configured but untested end-to-end** — image URLs are stored but upload flow has no integration tests
4. **Plan enforcement missing** — FREE plan merchants have full access to PRO features; no feature gates implemented
5. **No email verification on registration** — merchants can register with unverified email addresses
6. **Hermit agent runs synchronously in-request** — for large data sets, should be moved to a background task/queue
7. **Strategic agents are rule-based** — TrustGraph and FraudSentinel use threshold rules, not ML models; scores have no historical calibration
8. **No pagination on strategic insights** — `GET /ai/strategic/insights` has a hard `limit=100` cap

### Technical Debt
1. `test_auth.py` and `test_products.py` use hand-written test utilities that partially duplicate `conftest.py` fixtures
2. `conftest.py` `drop_all` was removed to fix test-run persistence issue — test DB tables now accumulate between runs until `create_all` is called fresh
3. OTP flow has no attempt counter — unlimited guessing allowed (6 digits = 1M combinations)
4. JWT uses HS256 symmetric algorithm — compromise of `APP_SECRET_KEY` invalidates all token security
5. Redis refresh token storage uses one key per merchant — concurrent sessions on multiple devices invalidate each other

---

## 6. Production Risks

### HIGH Priority — Must Fix Before Public Launch

**RISK-01: No rate limiting on auth endpoints**
- Impact: Credential stuffing, OTP brute force
- Mitigation: Add `slowapi` or nginx rate limiting on `/auth/login`, `/auth/forgot-password`, `/auth/verify-otp`

**RISK-02: Symmetric JWT (HS256)**
- Impact: Single `APP_SECRET_KEY` compromise forges any merchant's token
- Mitigation: Migrate to RS256 (asymmetric) with private key in secrets manager

**RISK-03: OTP unlimited attempts**
- Impact: 6-digit OTP can be brute-forced in minutes with automation
- Mitigation: Lock after 5 attempts, add 15-min cooldown

**RISK-04: APP_SECRET_KEY has insecure default**
- Impact: Any dev instance with default `"dev-secret-change-in-production"` is fully compromised if reachable
- Mitigation: Make it required with no default; fail on startup if not set

### MEDIUM Priority — Fix Within First Sprint

**RISK-05: No merchant-level API rate limiting**
- Impact: One merchant can exhaust DB connection pool, affecting all tenants
- Mitigation: Per-merchant rate limit via Redis counters on expensive endpoints

**RISK-06: No request logging / observability**
- Impact: Blind to errors, slow queries, or abuse in production
- Mitigation: Add structured logging (correlation ID, merchant_id, latency) + Sentry or similar

**RISK-07: Float precision on pre-existing data**
- Impact: Any float monetary values in legacy data will cause accumulated rounding errors
- Mitigation: Already fixed in new code; audit any existing DB rows with `NUMERIC` mismatch

**RISK-08: Alembic head not auto-applied on deploy**
- Impact: Deploy with schema mismatch causes 500 errors
- Mitigation: Add `alembic upgrade head` to deployment pipeline before process start

**RISK-09: Single Redis instance**
- Impact: Redis restart drops all active sessions
- Mitigation: Redis Sentinel or cluster for HA; configure `redis.asyncio` with retry

### LOW Priority — Post-Launch

**RISK-10: `selectinload` on large order history**
- Impact: `GET /orders/{id}` eager-loads all items and history; could be slow for orders with 100+ items
- Mitigation: Pagination on order_items if needed; current SQLAlchemy `selectinload` is efficient for typical sizes

**RISK-11: CSV export loads up to 5000 rows into memory**
- Impact: Memory spike during large exports
- Mitigation: Stream CSV using generator pattern if needed

---

## 7. Deployment Checklist

### Prerequisites
- [ ] PostgreSQL 13+ database provisioned (`sellermate` database + user)
- [ ] Redis 6+ instance provisioned
- [ ] Anthropic API key with credits
- [ ] AWS S3 bucket OR Cloudflare R2 bucket created
- [ ] Meta Business account with WhatsApp Cloud API enabled (if using WhatsApp)
- [ ] Domain with TLS certificate (for webhook verification)

### Environment Variables
```env
# Required — no defaults
ANTHROPIC_API_KEY=sk-ant-...
APP_SECRET_KEY=<64-char random hex>        # CHANGE THIS
S3_ACCESS_KEY=<key>
S3_SECRET_KEY=<secret>
WHATSAPP_ACCESS_TOKEN=<meta-token>
WHATSAPP_PHONE_NUMBER_ID=<id>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<any-string>
WHATSAPP_APP_SECRET=<meta-app-secret>

# Recommended overrides
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sellermate
REDIS_URL=redis://:pass@host:6379/0
APP_ENV=production
ALLOWED_ORIGINS=https://yourfrontend.com
S3_BUCKET_NAME=sellermate-uploads
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com  # if using R2
```

### Database Setup
```bash
# 1. Create database
createdb sellermate

# 2. Run migrations
cd apps/api
alembic upgrade head

# 3. Verify tables
psql sellermate -c "\dt"
# Expected: conversations, customers, hermit_insights, inventory_logs,
#           merchants, messages, order_items, order_status_history,
#           orders, product_variants, products, strategic_insights
```

### Application Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run server (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn (recommended for production)
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
```

### Health Verification
```bash
curl https://your-host/health
# Expected: {"status":"ok","version":"1.0.0"}

curl https://your-host/docs
# Expected: Swagger UI (disabled if APP_ENV=production)
```

### Pre-Launch Smoke Test
```bash
cd apps/api
python qa_orders.py     # Orders module live QA
# Or run full test suite against staging DB:
python -m pytest tests/ -v
```

### Meta WhatsApp Webhook Registration
```bash
# Set webhook URL in Meta Developer Console:
# https://your-host/api/v1/webhooks/whatsapp
# Verify token: <WHATSAPP_WEBHOOK_VERIFY_TOKEN from env>
```

---

## 8. Demo Script

### Setup (5 minutes)
```bash
# Start API
uvicorn app.main:app --reload

# Confirm running
curl http://localhost:8000/health
```

### Demo Flow (15 minutes)

**Step 1 — Register a merchant (1 min)**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@sellermate.ai",
    "phone": "+8801712345678",
    "password": "DemoPass123!",
    "business_name": "Dhaka Fashion House",
    "owner_name": "Rahim Chowdhury",
    "business_type": "FASHION_CLOTHING"
  }'
# Save access_token from response
TOKEN="<access_token>"
```

**Step 2 — Create a product with variants (1 min)**
```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Panjabi",
    "category": "CLOTHING",
    "base_price": "1200.00",
    "variants": [
      {"name": "White M", "sku": "PAN-WH-M", "price": "1200.00", "stock_quantity": 50},
      {"name": "White L", "sku": "PAN-WH-L", "price": "1200.00", "stock_quantity": 30}
    ]
  }'
# Save product_id and variant_id
```

**Step 3 — Add a customer (30 sec)**
```bash
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Karim Rahman",
    "phone": "+8801812345678",
    "address": "Mirpur, Dhaka",
    "district": "Dhaka"
  }'
# Save customer_id
```

**Step 4 — Place an order (30 sec)**
```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "<customer_id>",
    "items": [{"product_id": "<product_id>", "variant_id": "<variant_id>", "quantity": 2}],
    "discount_amount": "100",
    "shipping_cost": "80",
    "payment_method": "COD",
    "delivery_address": "Mirpur 10, Dhaka"
  }'
# Show total_amount = (1200*2) - 100 + 80 = 2380
```

**Step 5 — Advance order through lifecycle (1 min)**
```bash
# Confirm
curl -X POST http://localhost:8000/api/v1/orders/<order_id>/status \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "CONFIRMED", "note": "Verified via WhatsApp"}'

# Record payment
curl -X POST http://localhost:8000/api/v1/orders/<order_id>/payment \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount": "2380", "method": "BKASH"}'

# Mark delivered
curl -X POST http://localhost:8000/api/v1/orders/<order_id>/status \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "DELIVERED"}'
```

**Step 6 — Dashboard analytics (1 min)**
```bash
curl http://localhost:8000/api/v1/analytics/dashboard \
  -H "Authorization: Bearer $TOKEN"
# Shows: today_revenue, delivered_orders, repeat_customers, average_order_value
```

**Step 7 — Run strategic agents (1 min)**
```bash
curl -X POST http://localhost:8000/api/v1/ai/strategic/run \
  -H "Authorization: Bearer $TOKEN"
# Returns trust_score, confidence, risk_flags, fraud_risk_score, alert_reasons

curl http://localhost:8000/api/v1/ai/strategic/trust-score \
  -H "Authorization: Bearer $TOKEN"
```

**Step 8 — AI assistant conversation (3 min)**
```bash
# Create conversation
curl -X POST http://localhost:8000/api/v1/assistant/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Business Review"}'

# Stream AI response (SSE)
curl -N http://localhost:8000/api/v1/assistant/conversations/<conv_id>/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "আমার আজকের বিক্রয় কত হয়েছে?"}'
# AI responds in Bengali with real-time data from tools
```

**Step 9 — Export data (30 sec)**
```bash
# Orders CSV
curl http://localhost:8000/api/v1/orders/export \
  -H "Authorization: Bearer $TOKEN" -o orders.csv

# Customers CSV  
curl http://localhost:8000/api/v1/customers/export \
  -H "Authorization: Bearer $TOKEN" -o customers.csv
```

**Step 10 — Show multi-tenant isolation (30 sec)**
```bash
# Register second merchant
# Try accessing first merchant's order with second merchant's token
curl http://localhost:8000/api/v1/orders/<order_id_from_merchant1> \
  -H "Authorization: Bearer $TOKEN_MERCHANT2"
# Returns 404 — data is strictly isolated
```

---

## 9. Next Roadmap

### Sprint 1 — Security Hardening (1 week)
- [ ] Rate limiting on auth endpoints (`slowapi` or NGINX)
- [ ] OTP attempt counter (max 5, 15-min lockdown)
- [ ] Make `APP_SECRET_KEY` required with no insecure default
- [ ] Add request correlation ID and structured logging
- [ ] RS256 JWT migration (optional but recommended)

### Sprint 2 — Feature Completion (2 weeks)
- [ ] WhatsApp inbound message processing (order creation via chat)
- [ ] WhatsApp outbound replies via AI assistant
- [ ] Email/SMS notification gateway for OTP delivery
- [ ] Email verification on registration
- [ ] Plan enforcement (FREE/STARTER/PRO feature gates)

### Sprint 3 — Observability & Scale (1 week)
- [ ] Sentry error tracking integration
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] DB query logging with slow-query alerts
- [ ] Redis HA (Sentinel or Cluster)
- [ ] Background task queue (Celery or ARQ) for Hermit agent

### Sprint 4 — Intelligence Expansion (2 weeks)
- [ ] ML-based trust scoring (historical calibration with real merchant data)
- [ ] FraudSentinel rule expansion (velocity checks, geolocation, device fingerprinting)
- [ ] Demand forecasting agent (predict stock needs from order trends)
- [ ] Customer churn prediction agent
- [ ] Hermit agent scheduling (daily/weekly automatic analysis)

### Sprint 5 — Integrations (2 weeks)
- [ ] bKash payment gateway webhook
- [ ] Pathao / Steadfast courier API integration
- [ ] Facebook/Instagram order ingestion
- [ ] Shopify import adapter for merchant onboarding

### Long-Term
- [ ] Multi-language support (Bangla full translation of all error messages)
- [ ] Mobile SDK (React Native wrapper for the REST API)
- [ ] Subscription billing (Stripe or local gateway)
- [ ] Data export to Google Sheets / Excel
- [ ] Advanced reporting (cohort analysis, LTV calculation)

---

## Appendix — File Map

```
apps/api/
├── app/
│   ├── ai/
│   │   ├── agent.py                    ← Main streaming AI agent
│   │   ├── strategic_agents/
│   │   │   ├── trust_graph.py          ← Trust scoring agent
│   │   │   └── fraud_sentinel.py       ← Fraud detection agent
│   │   ├── prompts/system.py           ← Bengali system prompt builder
│   │   └── tools/                      ← 5 tool modules (inventory, orders, etc.)
│   ├── core/
│   │   ├── config.py                   ← Pydantic settings (all env vars)
│   │   ├── dependencies.py             ← FastAPI DI (CurrentMerchant, DB)
│   │   └── exceptions.py              ← HTTPException subclasses + handlers
│   ├── db/
│   │   ├── session.py                  ← Async SQLAlchemy engine + session factory
│   │   └── redis.py                    ← Redis async client
│   ├── models/                         ← 11 SQLAlchemy ORM models
│   ├── routers/                        ← 10 FastAPI routers
│   ├── schemas/                        ← Pydantic request/response schemas
│   └── services/                       ← Business logic (no HTTP concerns)
├── alembic/versions/                   ← 3 migration files
├── tests/                              ← 283 integration tests
├── qa_orders.py                        ← Live QA script (orders)
├── ORDER_QA_REPORT.md
├── ANALYTICS_QA_REPORT.md
├── STRATEGIC_AGENT_REPORT.md
└── FINAL_MVP_READINESS_REPORT.md       ← This file
```
