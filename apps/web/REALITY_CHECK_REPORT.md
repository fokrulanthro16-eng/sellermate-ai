# SellerMate AI — Reality Check Report

**Date:** 2026-06-23  
**Method:** Full code trace — backend service → API router → frontend hook → UI component  
**Scope:** No changes made. Read-only verification only.

---

## Verdict Summary

| Feature | Reality | Root Evidence |
|---------|---------|---------------|
| AI Assistant — Chat | PARTIALLY REAL | SSE streaming real; responses are rule-based local fallback, not AI |
| AI Assistant — Conversations/History | REAL | PostgreSQL `conversations` + `messages` tables |
| Trust Graph Agent | REAL | SQL queries on `orders` + `customers`; score ∝ data |
| Fraud Sentinel Agent | REAL | SQL queries on recent `orders`; score ∝ cancellations/stale unpaid |
| Dashboard — KPI cards | REAL | `analytics_service.get_dashboard()` — live SQL aggregations |
| Dashboard — Revenue chart (bars) | REAL | `date_trunc` SQL query on orders |
| Dashboard — Revenue chart X-axis labels | **FAKE** | `dataKey="period"` but API returns `date` — all labels blank |
| Dashboard — Order breakdown chart | REAL | `get_order_breakdown()` groups by `Order.status` |
| Dashboard — Top Products | REAL | `get_top_products()` joins `OrderItem + Order`, live data |
| Dashboard — Inventory health cards | REAL | `get_inventory_health()` counts `ProductVariant.stock_quantity` |
| Dashboard — AI insights banner | REAL | Reads from last `strategic_insights` record |
| Analytics — Revenue chart | REAL (data), **FAKE** (X-axis) | Same `date`/`period` field mismatch |
| Analytics — Order breakdown chart | REAL | Same service as dashboard |
| Analytics — Top Products | REAL | Same service as dashboard |
| Analytics — Customer metrics | REAL | `get_customer_metrics()` queries `Customer` table |
| Analytics — Granularity selector | **BROKEN** | Frontend sends `granularity=`, backend reads `period=`; backend always defaults to `day` |
| Orders — List | REAL | Paginated SQL with status/payment filters |
| Orders — Search | REAL | `search` param passed to backend |
| Orders — Status changes | REAL | `POST /orders/{id}/status` writes to DB |
| Orders — Payment recording | REAL | `POST /orders/{id}/payment` writes to DB |
| Products — List | REAL | Paginated SQL with `category` and `search` params |
| Products — Category filter | REAL | Passed to backend; backend filters on `Product.category` |
| Products — CRUD | REAL | Full create/update/delete endpoints exist |
| Inventory — Stock list | REAL | Queries `ProductVariant.stock_quantity` directly |
| Inventory — Low-stock alerts | REAL | `GET /inventory/alerts` — SQL where `qty <= threshold` |
| Inventory — Stock adjustment | REAL | `POST /inventory/adjust` writes to `ProductVariant` + `InventoryLog` |
| Customers — List | REAL | Paginated SQL with `search` param |
| Customers — Source filter | **PARTIALLY REAL** | Client-side filter on current page only; not sent to backend |
| Customers — CRUD | REAL | Standard POST/PATCH endpoints |
| Settings — Profile update | REAL | `PATCH /merchant/me` writes to `merchants` table |
| Language toggle (bn/en) | REAL | localStorage-backed; all sidebar/header labels switch |

---

## Detailed Findings

---

### 1. AI Assistant

**Verdict: PARTIALLY REAL**

#### What is Real
- Conversations are created in PostgreSQL (`conversations` table).
- Messages (user + assistant) are persisted in the `messages` table.
- History is fetched from DB and passed to the agent on each message.
- The SSE streaming pipeline is wired end-to-end:
  `POST /conversations/{id}/chat` → `assistant_service.stream_chat()` → `run_agent()` → `StreamingResponse(text/event-stream)`.
- Frontend correctly reads `data: {chunk}` SSE lines and renders them live.

#### What is Not Real AI
- `ANTHROPIC_API_KEY` is **empty** in `apps/api/.env`.
- `agent.py` (line 27-31) detects the empty key and routes 100% of requests to `fallback_assistant.py`.
- **All** assistant responses are from the local rule-based fallback, not Claude.
- The fallback queries the real database (orders, products, customers) and generates templated responses.
- It cannot: create orders, update stock, answer open-ended questions, or do multi-turn reasoning.

#### What the Fallback Does Right
- Detects Bangla vs English by Unicode range `[ঀ-৿]`.
- Queries live DB for today's revenue, pending orders, low-stock variants, top products.
- Responses change when the underlying data changes.

#### Fix Required
Set `ANTHROPIC_API_KEY` in `.env` or purchase API access. The wiring is complete and correct.

---

### 2. Trust Graph Agent

**Verdict: REAL**

Computed entirely from real DB queries in `trust_graph.py`:

| Signal | Source |
|--------|--------|
| Delivery rate | `COUNT(orders WHERE status=DELIVERED) / COUNT(orders - cancelled)` |
| Payment rate | `COUNT(orders WHERE payment_status=PAID) / COUNT(orders)` |
| Retention rate | `COUNT(customers WHERE total_orders > 1) / COUNT(customers)` |
| Cancel penalty | `COUNT(orders WHERE status=CANCELLED) / COUNT(orders)` |

Score is a weighted sum (base 50, adjustments ±10-25), clamped 0-100.

**Score will change when data changes.** If cancellations increase → score drops. If payment rate improves → score rises.

Result stored in `strategic_insights` table. Only refreshed when "Run Agents" button is clicked.

**One caveat:** Score is stale between runs. Dashboard banner shows the last stored score, not a live recalculation.

---

### 3. Fraud Sentinel Agent

**Verdict: REAL**

Computed from real DB queries in `fraud_sentinel.py` over the last 30 days:

| Pattern | Signal | Threshold |
|---------|--------|-----------|
| Cancellation spike | Recent cancelled / recent total | >50% → +40pts |
| Stale unpaid orders | Orders >7 days old, unpaid | ≥5 orders → +25pts |
| Order spike | Max single-day / avg daily ratio | ≥5× → +25pts |

**Score will change when data changes.** Add 10 cancellations → score increases. Mark unpaid orders as PAID → score decreases.

Same stale-score caveat as Trust Graph — only updates on "Run Agents" click.

---

### 4. Dashboard

**Verdict: REAL (with one broken display)**

All KPI computations in `analytics_service.get_dashboard()`:
- `today_revenue` → SQL `SUM(total_amount) WHERE date = today`
- `total_orders` → SQL `COUNT(orders)`
- `repeat_customers` → SQL `COUNT(customers WHERE total_orders > 1)`
- `average_order_value` → monthly_revenue / monthly_order_count
- `top_products` → JOIN on `order_items`, grouped by product
- `inventory_health` → `ProductVariant.stock_quantity` counts

#### Bug: Revenue Chart X-Axis Labels Are Blank

**File:** `apps/web/src/components/analytics/RevenueChart.tsx:40`

```tsx
<XAxis dataKey="period" />   // WRONG
```

**Backend** (`analytics.py schema`):
```python
class RevenuePoint(BaseModel):
    date: str   # ← field is "date"
    revenue: float
    orders: int
```

**Frontend type** (`types/index.ts:261`):
```typescript
export interface RevenuePoint {
  period: string;   // ← type says "period"
  revenue: number;
  orders: number;
}
```

The chart renders correct revenue amounts (the area/bars) but X-axis shows nothing because no item has a `period` key. The user sees a real revenue chart with invisible date labels.

**Revenue data is real. Date labels are blank.**

---

### 5. Analytics

**Verdict: REAL (with same X-axis bug + granularity bug)**

All analytics data comes from real SQL queries. Two additional bugs:

#### Bug 1: Same Revenue Chart X-axis Mismatch
Same `dataKey="period"` vs API `date` field issue as dashboard.

#### Bug 2: Granularity Selector Has No Effect

`useAnalytics.ts:21`:
```typescript
params: { from_date, to_date, granularity },  // sends "granularity"
```

`analytics.py:64`:
```python
period: str = Query("day", ...)   # reads "period", ignores "granularity"
```

The backend never receives the granularity change. It always processes data at `"day"` granularity. The period selector (7/30/90/180 days) correctly changes the date range, but the grouping is always daily.

Additionally, `dashboard/page.tsx` calls `useRevenue(from, to, "daily")` — passing `"daily"` instead of `"day"`. The value `"daily"` is silently ignored by the backend for the same reason; this accidentally works because the default is `"day"`.

---

### 6. Orders

**Verdict: REAL**

- List: paginated SQL, filtered by `status`, `payment_status`, `search`
- Status change: `POST /orders/{id}/status` → writes to DB + creates `OrderStatusHistory` record
- Payment: `POST /orders/{id}/payment` → updates `paid_amount`, `payment_status`
- Cancel: `DELETE /orders/{id}` → sets status to CANCELLED

All reads and writes go through real DB. No mock data anywhere in the chain.

---

### 7. Products

**Verdict: REAL**

- List: paginated SQL, filtered by `category`, `search`
- Category filter: passed as query param → `Product.category == category` in SQL
- CRUD: full create/edit/delete via `/products` endpoints
- Variants: create/delete on `/products/{id}/variants`

---

### 8. Inventory

**Verdict: REAL**

- List: reads `ProductVariant` + `Product` tables via `/inventory` endpoint
- Alerts: `GET /inventory/alerts` — SQL `WHERE stock_quantity <= low_stock_alert`
- Adjustment: `POST /inventory/adjust` → writes to `ProductVariant.stock_quantity` + creates `InventoryLog`
- Logs: `GET /inventory/logs` — paginated read of `InventoryLog` table

Health summary cards on the inventory page use `useInventoryHealth()` which calls `GET /analytics/inventory` — real DB counts.

---

### 9. Customers

**Verdict: PARTIALLY REAL**

- List: real paginated SQL with `search` parameter
- All customer data (name, phone, district, tags, totals) from DB
- CRUD: create/update/delete all work

#### Bug: Source Filter is Client-Side Only

```typescript
// customers/page.tsx:47
const filtered = source ? customers.filter((c) => c.source === source) : customers;
```

The `source` is never sent to the API. The filter applies only to the 24 customers on the current page. If there are 100 customers with 60 FACEBOOK sources spread across 5 pages, selecting FACEBOOK only shows matches on the current page (up to 24).

**Impact:** Source filter is unreliable for any dataset >24 customers. The customer data itself is real; the filter behavior is fake for larger datasets.

---

## Summary of All Bugs / Fake Implementations

| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | Revenue chart X-axis always blank | High | `RevenueChart.tsx:40` — `dataKey="period"` should be `dataKey="date"` |
| 2 | Granularity selector has no effect | Medium | `useAnalytics.ts:21` — param named `granularity` but backend reads `period` |
| 3 | Dashboard calls `useRevenue(from, to, "daily")` | Low | Should be `"day"` — silently ignored, accidentally works |
| 4 | Customer source filter is client-side only | Medium | `customers/page.tsx:47` — should be a backend query param |
| 5 | AI assistant uses rule-based fallback, not Claude | Critical | `apps/api/.env` — `ANTHROPIC_API_KEY=` is empty |
| 6 | Trust/Fraud scores are stale (no auto-refresh) | Low | Manual "Run Agents" required — no scheduled refresh |
| 7 | Frontend `RevenuePoint` type says `period` not `date` | Low | `types/index.ts:261` — causes TypeScript to accept wrong field name |

---

## Fix Priority

| Priority | Fix |
|----------|-----|
| **P0** | `RevenueChart.tsx:40` — change `dataKey="period"` to `dataKey="date"` |
| **P0** | `types/index.ts:261` — change `period: string` to `date: string` |
| **P1** | `useAnalytics.ts:21` — rename `granularity` to `period` in params |
| **P1** | `customers/page.tsx` — pass `source` to API as query param |
| **P2** | Set real `ANTHROPIC_API_KEY` for genuine AI responses |

---

## No Fake / Mocked Data Found In

- Order status/payment APIs — all real DB writes
- Product CRUD — all real DB writes  
- Inventory adjustment — confirmed writes `ProductVariant.stock_quantity`
- Strategic agent scoring formulas — all rule-based on real SQL aggregations
- Customer total_orders / total_spent — updated from seeder and from order creation
- Dashboard KPI numbers — all SQL aggregations, nothing hardcoded
- Conversation/message storage — real PostgreSQL rows
