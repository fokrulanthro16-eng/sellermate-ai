# HERMIT AGENT QA REPORT

**Run:** 2026-06-21  |  **Result:** 19/19 PASS

## What Was Built

Hermit Agent is a silent background intelligence layer added to SellerMate AI. It watches merchant data and produces hidden insights for dashboard/AI assistant use. It never sends messages automatically.

### New Files

| File | Purpose |
|------|---------|
| `app/models/hermit.py` | `HermitInsight` SQLAlchemy model + `InsightType`/`InsightSeverity` enums |
| `app/schemas/hermit.py` | `HermitInsightOut`, `HermitRunResult` Pydantic schemas |
| `app/services/hermit_service.py` | Analysis engine: 5 analyzers + `run_analysis` + `get_insights` + `mark_read` |
| `app/routers/hermit.py` | 3 endpoints: `/run`, `/insights`, `/insights/{id}/read` |
| `alembic/versions/b2c3d4e5f6a7_hermit_insights.py` | Migration: `hermit_insights` table + 2 ENUM types |

### Modified Files

| File | Change |
|------|--------|
| `app/models/__init__.py` | Added `HermitInsight` import for Alembic autogenerate |
| `app/main.py` | Mounted hermit router at `prefix="/api/v1/ai"` |

## API Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| `POST` | `/api/v1/ai/hermit/run` | JWT | Clear + regenerate all insights for merchant |
| `GET` | `/api/v1/ai/hermit/insights` | JWT | List insights (filterable) |
| `PATCH` | `/api/v1/ai/hermit/insights/{id}/read` | JWT | Mark a single insight as read |

### Query parameters for GET /insights

| Param | Type | Description |
|-------|------|-------------|
| `insight_type` | enum | Filter by type (SLOW_MOVING_PRODUCT, LOW_STOCK, REPEAT_BUYER, UNUSUAL_ORDER_PATTERN, WEEKLY_HEALTH) |
| `severity` | enum | Filter by severity (INFO, WARNING, CRITICAL) |
| `unread_only` | bool | Return only unread insights (default: false) |

Results ordered by severity (CRITICAL first) then generated_at descending.

## Analyzers

| Analyzer | Trigger | Severity |
|----------|---------|---------|
| `_analyze_slow_moving` | Active products ≥14 days old with zero non-cancelled orders in last 30 days | WARNING |
| `_analyze_low_stock` | Variants where `stock_quantity ≤ low_stock_alert` and `low_stock_alert > 0` | CRITICAL (if 0 stock) / WARNING |
| `_analyze_repeat_buyers` | Customers with ≥2 non-cancelled orders in last 30 days | INFO |
| `_analyze_unusual_orders` | Today's orders ≥2× the 7-day daily avg (spike) or 0 orders when avg ≥3 (drought) | INFO (spike) / WARNING (drought) |
| `_generate_weekly_health` | Revenue/orders/new-customers comparison: this week vs last week | INFO / WARNING (if revenue down ≥25%) |

## Database Model

```
hermit_insights
  id             STRING(36) PK
  merchant_id    STRING(36) FK → merchants.id CASCADE DELETE
  insight_type   ENUM(SLOW_MOVING_PRODUCT, LOW_STOCK, REPEAT_BUYER, UNUSUAL_ORDER_PATTERN, WEEKLY_HEALTH)
  severity       ENUM(INFO, WARNING, CRITICAL)
  title          STRING(255)
  body           TEXT
  meta           JSON
  is_read        BOOLEAN  default=false
  expires_at     TIMESTAMPTZ nullable
  generated_at   TIMESTAMPTZ server_default=now()

Indexes:
  ix_hermit_insights_merchant_id  (merchant_id)
  ix_hermit_insights_type         (merchant_id, insight_type)
  ix_hermit_insights_generated    (merchant_id, generated_at)
```

## Test Results

| # | Test | HTTP | Status |
|---|------|------|--------|
| 1 | T01 POST /run — no token → 401 | 401 | PASS |
| 2 | T01 GET /insights — no token → 401 | 401 | PASS |
| 3 | T02 POST /run (fresh merchant, no orders) | 200 | PASS |
| 4 | T03 GET /insights | 200 | PASS |
| 5 | T03 WEEKLY_HEALTH insight present | 200 | PASS |
| 6 | T03 Response schema validation | 200 | PASS |
| 7 | T04 GET /insights?insight_type=WEEKLY_HEALTH | 200 | PASS |
| 8 | T04 Filter returns only matching type | 200 | PASS |
| 9 | T05 GET /insights?severity=INFO | 200 | PASS |
| 10 | T05 Filter returns only matching severity | 200 | PASS |
| 11 | T06 GET /insights?unread_only=true | 200 | PASS |
| 12 | T06 All returned insights are unread | 200 | PASS |
| 13 | T07 PATCH /insights/{id}/read | 200 | PASS |
| 14 | T07 marked_read=true in response | 200 | PASS |
| 15 | T07 Marked insight removed from unread_only list | 200 | PASS |
| 16 | T07 PATCH /insights/nonexistent/read → 404 | 404 | PASS |
| 17 | T08 POST /run (2nd call — idempotency) | 200 | PASS |
| 18 | T08 Previous insights cleared before regeneration | 200 | PASS |
| 19 | T09 Merchant B cannot see Merchant A's insights | 200 | PASS |

## Design Decisions

- **No automatic dispatch** — insights are passive records. Only `POST /run` creates them; nothing triggers automatically.
- **Full regeneration on `/run`** — deletes all existing insights for the merchant, runs all 5 analyzers, bulk inserts fresh results. Ensures data is never stale and avoids accumulation.
- **Merchant isolation enforced at query level** — every query filters by `merchant_id` from the JWT; no cross-merchant data exposure.
- **`mark_read` endpoint** — third endpoint beyond the two required, added so the dashboard can dismiss insights without re-running analysis.
- **Severity sort** — CRITICAL → WARNING → INFO ordering via SQL CASE expression for dashboard display priority.

## Summary

- Tests executed: **19**
- Passed: **19**
- Failed: **0**
- Bugs found & fixed during development: **1** (login field name: `identifier` not `phone` in QA script)

Hermit Agent is fully operational. Auth, Merchant, and Product modules are unaffected.
