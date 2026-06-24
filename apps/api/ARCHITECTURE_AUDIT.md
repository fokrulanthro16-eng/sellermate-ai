# ARCHITECTURE AUDIT — SellerMate AI Backend

**Date:** 2026-06-21  
**Auditor:** Internal Technical Review  
**Scope:** All modules reviewed — Auth, Merchant, Products, Orders, Customers, Inventory, Analytics, AI Assistant, Hermit Agent, Webhooks  
**Files examined:** 40+ source files across models, schemas, services, routers, config, migrations, and tests

---

## Overall Score: 6.8 / 10

| Section | Score |
|---------|-------|
| 1. Authentication | 7.0 / 10 |
| 2. Merchant Module | 7.5 / 10 |
| 3. Hermit Agent | 7.0 / 10 |
| 4. Database Design | 7.5 / 10 |
| 5. API Design | 5.5 / 10 |
| 6. Security | 6.0 / 10 |
| 7. Scalability | 6.0 / 10 |
| 8. AI Readiness | 7.5 / 10 |
| 9. Multi-tenant Safety | 7.5 / 10 |
| 10. Production Readiness | 4.5 / 10 |

---

## 1. Authentication — 7.0 / 10

### Strengths
- bcrypt with 12 rounds — correct cost factor for 2026 hardware
- JWT access (15 min) + refresh (7 day) — industry-standard token lifecycle
- Refresh token rotation: one active token per merchant in Redis; old token rejected on reuse
- Access token blacklist on logout via Redis TTL — revocation works
- `decode_token` validates type claim (`"access"` vs `"refresh"`) — token substitution attacks blocked
- Dual-identifier login (`email` or `phone`) via single `identifier` field — good UX
- Bangladeshi phone regex enforced on registration and OTP flows
- Password validation: 8–128 chars, must contain digit and letter
- Suspended merchant blocked at the dependency level (`get_current_merchant`) on every request
- OTP lifecycle is correct: `verify_otp` reads only; `reset_password` atomically consumes

### Weaknesses
- **HS256 symmetric algorithm** — a single secret key compromise invalidates all tokens for all merchants. RS256 (asymmetric) would allow key rotation without revoking live sessions.
- **No rate limiting** — `POST /login`, `POST /forgot-password`, and `POST /verify-otp` are fully open. 6-digit numeric OTP has 1,000,000 combinations; at 10 requests/sec an attacker exhausts the space in ~28 hours within the 10-minute window.
- **OTP has no attempt counter** — no lockout after N wrong guesses.
- **No `jti` claim** — impossible to revoke an individual access token without blacklisting the full token string. Redis blacklist grows unboundedly (TTL helps but is imprecise).
- **`get_settings()` is `lru_cache`d** — test overrides require cache-clearing; secrets cannot be hot-rotated without restart.

### Technical Debt
- `tests/test_auth.py` references wrong response shapes: `data["access_token"]` instead of `data["tokens"]["access_token"]`, and `data["refresh_token"]` instead of `data["tokens"]["refresh_token"]`. The pytest suite would fail if run against the actual API. This is a regression risk — tests give a false sense of coverage.
- `_redis` is a module-level global singleton. Under multi-process uvicorn (e.g., `--workers 4`), each worker has its own in-memory fakeredis instance in dev, causing split-brain auth state.

### Recommended Improvements
1. Add `slowapi` rate limiter — 5 attempts/minute on login, 3/hour on forgot-password per IP.
2. Add OTP attempt counter in Redis (`otp_attempts:{phone}`) — lock after 5 wrong guesses.
3. Switch to RS256: generate a keypair, store private key in secrets manager.
4. Fix `test_auth.py` response path references immediately — the suite is currently misleading.
5. Add `jti` claim to access tokens and store active `jti` in Redis for proper per-token revocation.

---

## 2. Merchant Module — 7.5 / 10

### Strengths
- Full CRUD profile management with typed field updates
- Dashboard stats with prior-period comparison and percentage change
- Structured 4-step onboarding with step advancement tracking
- `onboarding_done` flag cleanly separates setup from active use
- Subscription plan tiers (FREE/STARTER/PRO) with expiry timestamp modeled
- Trust score field ready for gamification or credit scoring
- WhatsApp integration point exists (phone stored, HMAC signature wired)
- Cascade delete ensures complete tenant teardown
- Unique constraints on both email and phone at DB level

### Weaknesses
- **No email verification** — any email address can be used; users can impersonate domain owners.
- **Plan enforcement missing** — `SubscriptionPlan` field exists but is never checked in any route or service. A FREE merchant has identical access to a PRO merchant at the API level.
- **`complete_onboarding_step` accepts untyped `dict`** — step data has no schema. Sending any JSON for step 1 silently accepts it; only recognized keys are processed.
- **WhatsApp connect is a stub** — returns the current state with `qr_code: null`. No BSP integration, no QR generation.
- **`trust_score` is static at 50** — never updated by any service.
- **Dashboard stats query** — `ProductVariant.product.has(merchant_id=merchant_id)` triggers a correlated subquery that can be slow for merchants with many variants.

### Technical Debt
- Onboarding step handlers use raw `data["key"]` dict lookups — if a key is missing, the step silently does nothing. Should use typed Pydantic models per step.
- `DashboardStats` is missing `total_products` and `total_customers` — the full merchant overview requires two additional API calls to fill the dashboard.

### Recommended Improvements
1. Add email verification flow (send token to email on register; require verification before full access).
2. Add a plan-enforcement middleware or service that checks `plan` and `plan_expires_at` on protected routes.
3. Replace `OnboardingStepRequest.data: dict` with a `Union` of typed step schemas.
4. Add `total_products` and `total_customers` to `DashboardStats`.
5. Replace the correlated subquery in `get_dashboard_stats` with a direct JOIN.

---

## 3. Hermit Agent — 7.0 / 10

### Strengths
- Clean architecture: model → schema → service → router, fully separated
- Pure SQL analytics — no LLM dependency, deterministic, fast
- 5 distinct insight types each with semantically correct severity
- Merchant isolation enforced at every query
- Full regeneration on `/run` prevents stale insight accumulation
- Three composite indexes for merchant-scoped lookups
- `expires_at` field models insight lifecycle (weekly health expires after the week)
- `mark_read` endpoint gives the dashboard a proper read lifecycle

### Weaknesses
- **No scheduled trigger** — `/run` requires a manual HTTP call. Insights go stale immediately after generation and will never update unless the dashboard or a cron calls `/run`.
- **Race condition on concurrent `/run` calls** — both requests execute `DELETE FROM hermit_insights WHERE merchant_id = X` then both INSERT; the result is doubled insights or empty set depending on timing. No advisory lock or upsert strategy.
- **Timezone mismatch** — `this_week_start` is computed as UTC Monday 00:00. Bangladesh is UTC+6, so the week starts Saturday afternoon UTC. All weekly health data is off by 6 hours.
- **Expired insights are never pruned** — `expires_at` is modeled but never queried. Expired insights show in GET /insights unless filtered by the caller.
- **No pagination on GET /insights** — returns all insights for a merchant in one response. A merchant who calls `/run` frequently could accumulate many insights before a full flush.
- **Hardcoded thresholds** — `daily_avg < 2`, spike = `2×`, drought = 0 when avg ≥ 3. These are not configurable per merchant or per plan.
- **Slow-moving analyzer fires on all merchants** — a merchant with zero products still runs all 5 analyzers on `/run`.

### Technical Debt
- No pytest coverage for Hermit. The hermit service is tested only via manual QA scripts.
- `_generate_weekly_health` has a nested async function (`_week_stats`) — fine for Python but adds nesting depth. Should be module-level or method-level helper.

### Recommended Improvements
1. Add a Celery Beat task or APScheduler job that calls `run_analysis` for all active merchants nightly at 3am Bangladesh time (UTC+6).
2. Add an advisory lock or `SELECT FOR UPDATE SKIP LOCKED` pattern in `run_analysis` to prevent double-execution.
3. Fix timezone: use `pytz` or `zoneinfo` (`Asia/Dhaka`) for week boundary calculation.
4. Add `?include_expired=false` filter to GET /insights and auto-exclude where `expires_at < now()`.
5. Add pytest tests: at minimum test `_analyze_low_stock` and `_generate_weekly_health` with mock DB data.

---

## 4. Database Design — 7.5 / 10

### Strengths
- 9 well-normalized tables covering all core domains
- UUID PKs throughout — no sequential ID leakage, globally unique across shards
- PostgreSQL-native types: `ARRAY(String)` for image URLs, `JSON` for flexible attributes, `ENUM` for controlled vocabularies
- Composite indexes on all high-cardinality merchant-scoped filter patterns
- ON DELETE CASCADE on all FKs — tenant deletion is clean and complete
- `TimestampMixin` applied consistently to all major entities
- `InventoryLog` as append-only audit trail with before/after quantities
- `OrderStatusHistory` for full state change tracking
- `expire_on_commit=False` prevents lazy-load failures in async context
- `pool_pre_ping=True` for connection health validation

### Weaknesses
- **`String(36)` PKs instead of PostgreSQL native `UUID` type** — wastes 8 bytes per row vs native UUID, uses string comparison instead of integer comparison in B-tree indexes.
- **No check constraints** — the DB accepts `total_amount = -500`, `stock_quantity = -10`. Application code prevents this, but the DB is not the source of truth for constraints.
- **`Product.total_sold` counter is never updated** — `order_service.py` does not increment it on order creation. Any query or UI relying on this field sees 0 for all products forever.
- **`Customer.total_orders` and `total_spent` are denormalized** — updated on order creation but not decremented on cancellation. A cancelled order permanently inflates customer spend stats.
- **No optimistic locking on stock** — two concurrent orders for the same variant both pass the stock check (`variant.stock_quantity >= qty`) before either deducts. Race condition allows overselling.
- **`_generate_order_number` is not atomic** — `COUNT(*) + 1` under concurrent inserts produces duplicate order numbers. The `order_number` column has `unique=True` which would raise a DB error, but the error is not handled gracefully.
- **`hermit_insights` rows never expire** from DB — `expires_at` is application-only; DB has no scheduled cleanup.

### Technical Debt
- `alembic/env.py` should import `app.models` to ensure all model changes are detected by autogenerate. Currently models are imported manually in `__init__.py`.
- No `CHECK` constraints on numeric fields for non-negative enforcement.
- `Product.image_urls: ARRAY(String)` — correct for simple storage but limits future image metadata (size, alt text, order).

### Recommended Improvements
1. Replace `String(36)` PKs with `UUID` type via `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)`.
2. Add check constraints: `total_amount >= 0`, `stock_quantity >= 0`, `quantity >= 1`.
3. Fix `product.total_sold`: increment in `order_service.create_order` and decrement in `cancel_order`.
4. Fix `Customer.total_spent` / `total_orders`: update on cancellation with proper subtraction.
5. Add optimistic locking for stock: use `UPDATE product_variants SET stock_quantity = stock_quantity - :qty WHERE id = :id AND stock_quantity >= :qty` and check `rowcount == 1`.
6. Fix order number generation: use `SELECT nextval(sequence)` or a per-merchant sequence.

---

## 5. API Design — 5.5 / 10

### Strengths
- Consistent response envelopes: `{"success": true, "data": {...}}` and `{"success": false, "error": {"code": N, "message": "..."}}`
- Pagination with full meta (`page`, `limit`, `total`, `total_pages`) on all list endpoints
- Semantically correct HTTP status codes throughout (201 create, 204 delete, 409 conflict, 422 validation)
- Pydantic v2 response models on every route — schema is self-documenting
- SSE streaming for AI chat — correct for real-time LLM output
- CSV export for orders — practical operational feature
- Analytics endpoints support date-range queries with period bucketing

### Weaknesses
- **Double-prefix URL bug (critical)** — every router declares its own `prefix` AND is mounted with the same prefix. Result: all endpoints have duplicated path segments:
  - Auth: `/api/v1/auth/auth/login`
  - Merchant: `/api/v1/merchant/merchant/me`
  - Products: `/api/v1/products/products/`
  - Orders: `/api/v1/orders/orders/`
  - This is the current working state (QA tests pass against these URLs) but the URLs are non-standard. Any frontend or API client built against these paths becomes locked to the bug.
- **Analytics date parsing is fragile** — `datetime.fromisoformat(from_date)` with a plain `YYYY-MM-DD` string raises `ValueError` on bad input, returning HTTP 500 instead of 422.
- **No OpenAPI security scheme** — the `Bearer` token requirement is not declared in the OpenAPI spec. Swagger UI `/docs` shows no "Authorize" button.
- **`GET /merchant/stats` returns only today's data** — dashboard is missing all-time totals (`total_products`, `total_customers`).
- **WhatsApp webhook `_handle_inbound_message` is `pass`** — inbound WhatsApp messages are silently swallowed. No error, no log.
- **CSV export truncates at 5,000 rows silently** — a merchant with 5,001 orders receives a file without the last order and no warning.
- **No request/response correlation ID** — impossible to trace a specific request through logs.

### Technical Debt
- Double-prefix URLs are the single most disruptive debt item: fixing it requires updating all clients simultaneously.
- No API changelog or deprecation strategy defined.

### Recommended Improvements
1. **Fix the double-prefix router mounting immediately** — routers should either define a prefix or be mounted with one, not both. Recommended: remove prefix from all `APIRouter()` declarations and mount them in `main.py` with the full path.
2. Add try/except around analytics date parsing, returning 422 with a clear message.
3. Declare `HTTPBearer` security scheme in `main.py` FastAPI constructor (`openapi_extra`).
4. Add `X-Request-ID` header middleware (UUID per request, echoed in response).
5. Replace silent CSV truncation with a `Link: </orders/export?page=2>` header or a 206 Partial Content response.

---

## 6. Security — 6.0 / 10

### Strengths
- bcrypt 12 rounds — correct; not MD5, not SHA1
- JWT type discrimination (`"access"` vs `"refresh"`) prevents cross-type substitution
- Token blacklist on logout — revocation is implemented, not just claimed
- HMAC-SHA256 signature on WhatsApp webhooks (when `whatsapp_app_secret` is configured)
- CORS origin whitelist — not wildcard `*`
- Merchant isolation enforced on every DB query via JWT-derived `merchant_id`
- `WWW-Authenticate: Bearer` returned on 401 — RFC 6750 compliant
- Pydantic validation on all request bodies — no raw dict access from user input

### Weaknesses
- **No rate limiting anywhere** — the entire API is open to automated abuse. Login brute-force, OTP exhaustion, and account enumeration are all possible.
- **WhatsApp webhook signature is optional** — if `whatsapp_app_secret` is empty (as in the current `.env`), the HMAC check is skipped entirely. Any POST to `/webhooks/whatsapp` is accepted without authentication.
- **SQL echo in non-production** — `echo=not settings.is_production` logs all SQL including values, which may include names, phone numbers, and order data in dev logs. Problematic if dev logs are forwarded to a log aggregator.
- **AI `adjust_stock` tool is write-enabled** — a prompt injection in a customer-generated product name or note could instruct the AI to zero out stock across a merchant's catalog. No write-tool authorization separate from chat authorization.
- **`LRU_CACHE` on settings** — if secrets are rotated, the old secret stays active until the process restarts.
- **Anthropic API key is empty in `.env`** — server starts and accepts requests; first AI call fails with an unhandled upstream error (no graceful degradation message).
- **No input size limit** — no `Content-Length` guard; `chat` endpoint accepts arbitrarily large messages that get forwarded to the LLM.
- **`dev-secret-key`** in the default Settings class — if `APP_SECRET_KEY` is not set, the fallback is a known public string. All JWTs become forgeable.

### Technical Debt
- HMAC check conditionality in the webhook handler is a security anti-pattern; the check should be mandatory in production and an explicit startup error if unconfigured.

### Recommended Improvements
1. Add `slowapi` middleware: 10 req/min on auth, 3 req/min on OTP endpoints, global 100 req/min per IP.
2. Make `whatsapp_app_secret` required in production (validate in `Settings.model_post_init`).
3. Disable SQL echo completely in all environments; use a structured query logger instead.
4. Add a `MaxBodySize` middleware (1MB cap on all endpoints except file upload).
5. Add LLM tool authorization: separate `read_tools` and `write_tools`; require explicit user consent for write tools.
6. Add startup validation: raise `RuntimeError` if `ANTHROPIC_API_KEY` is empty and the assistant router is mounted.
7. Strip `APP_SECRET_KEY` default from `Settings` class — fail fast with a clear error if not set.

---

## 7. Scalability — 6.0 / 10

### Strengths
- Fully async throughout: FastAPI + SQLAlchemy 2.x async + asyncpg + redis.asyncio + LangChain async
- Connection pool: 20 base + 10 overflow = up to 30 concurrent DB connections per worker
- `pool_pre_ping=True` rejects stale connections before use
- hiredis C extension for Redis serialization
- LangChain streaming SSE — AI output doesn't block the response
- All list endpoints paginated — no unbounded queries
- Composite indexes on merchant-scoped filters — queries stay O(log N) per tenant

### Weaknesses
- **Order number generation race condition** — `COUNT(*) + 1` is not atomic; concurrent order creation produces duplicate numbers. `unique=True` constraint causes a hard 500, not a retry.
- **Hermit `/run` full delete-then-insert** — under load (1000 merchants all calling `/run` concurrently), this produces 1000 table-scans + bulk DELETEs + bulk INSERTs simultaneously. No batching, no queue.
- **`export_csv` loads 5000 rows into Python memory** — blocks a DB connection and an asyncio task for the full export duration. No streaming CSV write.
- **No background job queue** — all processing is synchronous to the HTTP request. Long AI calls, Hermit runs, and exports all hold uvicorn workers.
- **Single Redis instance** — no sentinel or cluster. Redis is the single point of failure for auth (blacklist, refresh tokens, OTPs).
- **No read replicas** — analytics and Hermit queries compete with write traffic on the same connection pool.
- **AI agent has no timeout or tool call limit** — a slow/looping LLM call holds the DB connection open for the duration.
- **Global `_redis` singleton** — multiple uvicorn workers (`--workers N`) each have their own singleton. In dev (fakeredis), auth state is not shared between workers, causing random auth failures.
- **No response caching** — identical analytics queries (same merchant, same date range) hit the DB every time.

### Technical Debt
- The current architecture is designed for a single-process deployment. Scaling horizontally requires fixing the Redis singleton, adding a proper connection-per-request pattern, and moving Hermit to a background queue.

### Recommended Improvements
1. Replace `_generate_order_number` with a per-merchant PostgreSQL sequence or `SELECT nextval()`.
2. Add Celery + Redis broker for background tasks (Hermit runs, exports, future notifications).
3. Move `get_redis()` to return a per-request client from a pool (use `redis.asyncio.ConnectionPool`).
4. Add `anyio.move_on_after(30)` timeout around AI agent calls.
5. Add a Redis read-through cache (5-minute TTL) on analytics overview and revenue series queries.
6. Use `asyncio.StreamWriter` pattern for CSV export instead of loading 5000 rows into memory.

---

## 8. AI Readiness — 7.5 / 10

### Strengths
- LangChain ReAct tool-calling loop — the agent can chain multiple tool calls before responding
- 5 tool modules covering the full merchant domain (inventory, orders, customers, products, analytics)
- Bilingual system prompt (Bangla + English) — critical for Bangladeshi f-commerce target market
- SSE streaming delivers real-time character-by-character output to the frontend
- Conversation history persisted in DB — context survives page refresh
- `tool_calls` and `tool_results` stored in `Message` model — full audit trail of AI actions
- `input_tokens` / `output_tokens` fields in Message — cost tracking foundation
- Hermit Agent as passive intelligence completely decoupled from the interactive assistant
- Merchant-scoped tool closures — tools cannot access cross-tenant data by construction

### Weaknesses
- **Hardcoded model (`claude-haiku-4-5-20251001`)** — Haiku is the cheapest/fastest model; complex multi-step reasoning may produce errors. No way to upgrade per-merchant or per-request without a code change.
- **`today_stats` never populated in `stream_chat`** — `run_agent` accepts `today_stats` for the system prompt but `assistant_service.stream_chat` always passes `{}`. The system prompt shows 0 revenue and 0 orders.
- **Hermit insights not injected into agent context** — the AI assistant cannot answer "what are my pending alerts?" because it has no tool to read Hermit insights.
- **History truncated at last 20 messages** — older context is silently dropped. For merchants with long support sessions, the agent forgets earlier parts of the conversation.
- **No tool call budget** — the agent loop has no max_iterations guard. A confused LLM could call tools in an infinite loop.
- **Write tools in the agent without additional confirmation** — `adjust_stock` directly mutates inventory. A jailbroken or confused response could drain a merchant's stock.
- **`ai/graph.py` and `ai/state.py` exist but are unused** — LangGraph is imported and installed but the agent does not use the graph API. This is dead code / work-in-progress that adds dependency weight.
- **No graceful degradation** when Anthropic API is unavailable — the SSE stream emits an unhandled exception traceback.

### Technical Debt
- The agent uses a bare `while True` loop with `if not tool_calls: break`. Needs a `max_iterations` guard.
- LangGraph is in `requirements.txt` but not used. Either remove it or commit to the graph-based architecture.

### Recommended Improvements
1. Populate `today_stats` in `stream_chat` by calling `merchant_service.get_dashboard_stats` before the agent loop.
2. Add a `get_hermit_insights` tool that reads the merchant's current insights from the DB.
3. Add `max_iterations=10` to the agent loop and emit a friendly "I'm having trouble completing this" message on limit.
4. Add try/except around `run_agent` in `stream_chat`, yielding a structured error SSE event on failure.
5. Make the model configurable in `Settings` (`ai_model: str = "claude-haiku-4-5-20251001"`) with plan-gated upgrades to Sonnet for PRO merchants.
6. Remove `langgraph` from dependencies or migrate the agent to use it properly.

---

## 9. Multi-tenant Safety — 7.5 / 10

### Strengths
- `CurrentMerchant` dependency resolves `merchant_id` from JWT on every protected request — no merchant ID accepted from request body
- Every service function receives `merchant_id` as a parameter and filters all queries against it
- AI tool closures bind `merchant_id` at construction — tools structurally cannot escape the tenant boundary
- ON DELETE CASCADE on all child FKs — complete cleanup on merchant deletion
- Customer `phone` is unique per merchant (not globally) — correct multi-tenant phone semantics
- Order numbers are prefixed and sequenced per merchant
- Hermit insights are triple-filtered by merchant (model FK, every query WHERE, and GET endpoint)
- No cross-tenant joins in any service

### Weaknesses
- **No PostgreSQL row-level security (RLS)** — the application is the only enforcement layer. A single SQL construction bug (e.g., in a future dynamic query) would expose cross-tenant data at the DB level.
- **Conversations list returns last 50 with no pagination** — a high-volume merchant silently loses access to older conversations via the API.
- **WhatsApp webhook has no merchant routing** — `_handle_inbound_message` is a `pass` stub. When implemented, matching inbound WhatsApp messages to the correct merchant (via `phone_number_id`) will be critical to avoid cross-merchant message attribution.
- **Hermit `/run` race condition** — two simultaneous calls from the same merchant corrupt insights (double-insert or empty set after both DELETEs).
- **`Product.total_sold` is always 0** — any analytics or AI response using this field gives wrong answers for all merchants equally.

### Technical Debt
- No automated cross-tenant isolation tests. The QA suite tests that Merchant B cannot read Merchant A's products, but no other cross-tenant scenarios are tested (orders, customers, conversations, insights).

### Recommended Improvements
1. Enable PostgreSQL RLS on all tables with a `merchant_id` column — even a simple `USING (merchant_id = current_setting('app.tenant_id'))` policy adds a DB-level safety net.
2. Add pagination to `list_conversations` (default 20 per page).
3. Add a cross-tenant isolation test fixture that creates 3 merchants and asserts no data leakage across all modules.
4. Fix Hermit `/run` race condition with a Redis distributed lock (`SET NX PX 30000` on `hermit_lock:{merchant_id}`).

---

## 10. Production Readiness — 4.5 / 10

### Strengths
- `is_production` flag gates SQL echo, fake Redis, and API docs
- bcrypt and PyJWT are production-grade cryptographic libraries
- Pydantic v2 strict input validation on all endpoints
- Alembic migrations with version chain
- `pool_pre_ping=True` prevents dead-connection surprises
- CORS explicitly configured (not wildcard)
- `/health` endpoint exists

### Weaknesses
- **No Dockerfile or docker-compose** — the service cannot be containerized or deployed without custom work.
- **No CI/CD** — no `.github/workflows`, no test runner, no lint check, no migration gate.
- **`pytest` suite is broken** — `test_auth.py` accesses `data["access_token"]` (wrong path); all login-dependent tests would fail. The suite provides false confidence.
- **No structured logging** — all output is uvicorn's default text format. No JSON logs, no log levels per module, no request IDs.
- **No error monitoring** — no Sentry, no Datadog, no Rollbar. Production errors are invisible without manual log inspection.
- **`/health` endpoint does not check dependencies** — returns `{"status": "ok"}` even if PostgreSQL and Redis are unreachable. A load balancer health check would pass through a completely broken backend.
- **No startup validation** — `ANTHROPIC_API_KEY`, `APP_SECRET_KEY`, and `DATABASE_URL` are not required at startup. The server starts with bad config and fails at runtime.
- **WhatsApp webhook signature is skipped** if `whatsapp_app_secret` is unset (which it is in the current `.env`).
- **Double-prefix URL bug** is baked into the running API — any frontend built against these URLs inherits the bug.
- **No graceful shutdown** — SSE AI streaming sessions are cut off immediately on `SIGTERM`.

### Technical Debt
- The gap between "QA-tested and working" and "production deployable" is approximately 3–4 weeks of infrastructure work.

### Recommended Improvements
1. Write a `Dockerfile` (multi-stage: build + slim runtime) and `docker-compose.yml` with postgres, redis, and api services.
2. Add GitHub Actions CI: `ruff check`, `mypy`, `pytest` on every PR; fail the PR if any fail.
3. Fix `test_auth.py` response path references — this is a one-hour fix.
4. Replace `/health` with a deep health check: ping DB (`SELECT 1`) and Redis (`PING`), return 503 if either fails.
5. Add `startup_validation()` in the `lifespan` function: assert required secrets are non-empty and non-default.
6. Add `structlog` or configure Python `logging` in JSON format with `request_id` field propagated from middleware.
7. Integrate Sentry: `sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)`.

---

## Readiness Estimates

### MVP Readiness — **68%**

All eight core modules are implemented and manually QA-tested. Auth, Merchant, Products, Orders, Customers, Inventory, Analytics, and the AI Assistant function end-to-end. Hermit Agent is a complete bonus feature.

**Blocking gaps:**
- Double-prefix URL bug makes the API contract non-standard
- pytest suite is broken (false coverage signal)
- No deployment artifacts (Docker, CI/CD)
- No rate limiting on any endpoint
- `today_stats` never populated in AI system prompt (degraded AI UX)

**Estimate to close:** 2–3 weeks of focused engineering.

---

### Production Readiness — **32%**

The backend can handle a demo. It cannot safely handle paying customers.

**Critical blockers:**
- No rate limiting (brute-force attack surface)
- No error monitoring (blind to production failures)
- No structured logging (undebuggable incidents)
- No Docker / deployment pipeline
- No database check constraints (data integrity at risk)
- Broken test suite (no regression safety net)
- Race conditions in order creation and stock deduction
- Oversell vulnerability in concurrent order flow

**Estimate to close:** 6–8 weeks, including infrastructure, hardening, and test coverage.

---

### Seed-Stage Readiness — **62%**

Sufficient for investor demos, design partner pilots, and controlled beta with 10–20 merchants. The product story is coherent: auth, merchant management, full order lifecycle, AI assistant, and background intelligence all exist.

**What's needed before first paying customers:**
- Fix the double-prefix URL bug before any frontend is built against these paths
- Fix the pytest suite
- Add basic rate limiting
- Add a deep health check
- Fix `today_stats` in AI chat
- Add Docker + a one-command local setup

**Estimate to first beta:** 3–4 weeks.

---

### Merchant Scale Projections

| Scale | Supported? | Limiting Factor |
|-------|-----------|----------------|
| **100 merchants** | **Yes — comfortably** | Pool size 20+10 is more than adequate. Redis singleton is stable. Single-process uvicorn handles load trivially. |
| **1,000 merchants** | **Marginal — with risk** | Pool may saturate under concurrent peak. Order number race condition becomes real. Hermit bulk-refresh for 1K merchants simultaneously would be painful. Analytics queries slow without read replica. Rate limiting absence becomes dangerous. |
| **10,000 merchants** | **No — requires architectural changes** | Connection pool is the hard limit (30 connections, shared by all). Need: Redis cluster, connection pool per service, read replicas, background job queue (Celery), response caching, and Hermit scheduler. Estimated 8–12 weeks of infrastructure re-work. |

**Path to 10K merchants requires:**
1. Horizontal uvicorn workers with pgBouncer connection pooler
2. PostgreSQL read replica routing for analytics and Hermit queries
3. Redis Cluster (3 node minimum) for auth state
4. Celery + Redis broker for background jobs (Hermit, exports, notifications)
5. Response caching layer (Redis) for analytics with 5-minute TTL
6. Fix all race conditions (order number, stock deduction, Hermit run)
7. Per-tenant rate limiting instead of per-IP

---

## Executive Summary

SellerMate AI is a well-architected, feature-complete MVP backend for Bangladeshi f-commerce merchants. The technology choices are modern and appropriate: FastAPI async, SQLAlchemy 2.x, PostgreSQL, Redis, bcrypt, JWT, LangChain, and Anthropic's Claude. The domain model is thorough — nine tables covering merchants, products, variants, orders, customers, inventory logs, analytics, AI conversations, and the novel Hermit insights system.

**What the team built correctly:**
The merchant isolation pattern is consistent and correct across all modules. The AI assistant is genuinely useful — bilingual, tool-calling, streaming, with full conversation history. The analytics layer covers revenue, orders, products, and inventory health. The Hermit Agent is architecturally sound as a passive intelligence layer. The QA process caught and fixed multiple real bugs during development.

**The three critical issues that must be fixed before external use:**
1. **Double-prefix URL mounting bug** — `/api/v1/auth/auth/login` instead of `/api/v1/auth/login`. If a frontend is built against the current URLs, fixing this becomes a breaking change. Fix it now while there is no client.
2. **No rate limiting** — the authentication and OTP endpoints are fully open to automated abuse. This is not acceptable even in a private beta.
3. **Broken pytest suite** — `test_auth.py` references the wrong response structure and would fail if run. Tests are the only regression safety net; they need to pass.

**The architectural risk that limits scale:**
The concurrent stock deduction race condition. Two orders arriving simultaneously for the same product pass the stock availability check before either deducts, enabling oversell. This is a data integrity issue, not just a performance issue. It needs an atomic `UPDATE ... WHERE stock_quantity >= qty RETURNING id` pattern.

**The honest assessment:**
This backend is impressive for its stage. It has more working features than most seed-stage startups launch with. The code quality is consistent, the service separation is clean, and the AI integration is production-grade in design. With 4 weeks of hardening work (Docker, rate limiting, race condition fixes, test suite repair, structured logging, deep health checks), this backend can support a real private beta. With 8 weeks of infrastructure work, it can support 1,000 merchants in production.

| Readiness | Score |
|-----------|-------|
| MVP Demo | 68% |
| Private Beta (10–50 merchants) | 58% |
| Seed-Stage Fundraising Demo | 85% |
| Production / First Paying Customers | 32% |
| 100-Merchant Scale | 80% |
| 1,000-Merchant Scale | 40% |
| 10,000-Merchant Scale | 15% |
