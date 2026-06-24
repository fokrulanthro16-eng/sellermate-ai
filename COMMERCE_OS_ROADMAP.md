# SellerMate Commerce OS — Engineering Roadmap

> Transform SellerMate from inventory software into an AI-powered Commerce Operating System for Bangladeshi e-commerce.

---

## Current State Audit

### What's Done
| Area | Status | Notes |
|------|--------|-------|
| Backend API (FastAPI) | ✅ Complete | Auth, products, orders, customers, inventory, analytics, strategic |
| Database (PostgreSQL + SQLAlchemy) | ✅ Complete | All models, async queries |
| Premium CSS design system | ✅ Complete | Glassmorphism, dark/light, animations |
| Dashboard page | ✅ Premium | AI banner, KPI cards, inventory health |
| Analytics page | ✅ Premium | Revenue chart, donut orders, top customers |
| AI Center page | ✅ Premium | Trust/Fraud tabs with SVG gauges |
| Intent detector | ✅ Complete | rapidfuzz + 12 intent classes |
| Package AI engine | ✅ Complete | numpy trend, real DB, bilingual |
| TrustGraph agent | ✅ Complete | delivery, payment, retention scoring |
| FraudSentinel agent | ✅ Complete | cancellation spike, stale unpaid, order spike |
| GrowthCoach agent | ✅ Complete | MoM revenue, trend slope, concentration risk |
| MarginGuardian agent | ✅ Complete | COD ratio, refund rate, discount depth, unpaid exposure |
| DemandOracle agent | ✅ Complete | velocity per SKU, days-to-stockout |
| LangContext + i18n.ts | ✅ Complete | bn/en with localStorage persistence |
| Sidebar + Header | ✅ Premium | Language toggle, theme toggle |

### What's Missing / Incomplete
| Area | Gap | Impact |
|------|-----|--------|
| **Orders page** | Old UI, no bilingual | High |
| **Products page** | Old UI, categories hardcoded Bangla | High |
| **Customers page** | Old UI, no bilingual | High |
| **Inventory page** | Old UI, no bilingual | High |
| **Assistant page** | Basic UI, no t() usage, no context memory | High |
| **Settings page** | Basic UI, hardcoded Bangla | Medium |
| **Products/Orders detail pages** | No bilingual | High |
| **All table headers** | Hardcoded Bangla | High |
| **All form labels** | Hardcoded Bangla | High |
| **Status badges** | Hardcoded Bangla | Medium |
| **AI context memory** | Fresh context every message | High |
| **Credit Readiness agent** | Not built | Medium |
| **New agents in AI Center UI** | Growth/Margin/Demand not shown | Medium |
| **AI Center — 5 agent tabs** | Only 2 tabs | Medium |

---

## Architecture Principles

```
Commerce OS Stack
├── Backend: FastAPI async + PostgreSQL + Redis
├── AI Layer: Package Engine (no API key) → Gemini → Claude
├── Frontend: Next.js 15 App Router + TanStack Query v5
├── Design: Tailwind CSS + custom premium tokens + next-themes
└── i18n: LangContext t() — single source of truth, no hardcoded strings
```

**Hard rules for all future work:**
- Every string visible to the user goes through `t()` or `label(bn, en)`
- No hardcoded Bangla outside `i18n.ts`
- No invented numbers in AI responses — all metrics from real DB
- No new backend routes unless strictly required
- No breaking changes to existing API contracts

---

## Phase 1 — Complete Bilingual Support

**Goal:** Every visible string responds to the language toggle. User switches EN → BN and every label, placeholder, table header, badge, and message changes.

**Scope:** All 6 core pages + 3 detail pages + all shared components.

### 1.1 — i18n.ts expansion

Add missing translation keys to `apps/web/src/lib/i18n.ts`:

```typescript
// Orders
statusAll, statusPending, statusConfirmed, statusProcessing,
statusShipped, statusDelivered, statusCancelled, statusReturned,
payAll, payUnpaid, payPartial, payPaid, payRefunded,
orderNumber, customer, amount, paymentMethod, deliveryDistrict,
searchOrders, quickFilter, today, thisWeek, cancelRate,

// Customers
sourceAll, sourceFacebook, sourceWhatsapp, sourceInstagram,
sourceManual, sourceWalkIn, totalSpent, lastOrder, orderCount,
phone, district, addNote, vipTag,

// Products
categories (10 Bangladeshi categories), viewGrid, viewTable,
sku, variants, stock, price, cost, margin, addVariant,
productName, category, description, images,

// Inventory
adjustStock, adjustmentType, adjustmentReason, currentStock,
restock, shrinkage, damaged, correction, lowStockThreshold,
velocity, daysLeft, urgency, critical, high, medium, low,

// AI Center (new agents)
growthCoach, marginGuardian, demandOracle, creditReadiness,
growthScore, marginScore, restockScore, creditScore,
trendGrowing, trendStable, trendDeclining,
codRatio, refundRate, discountRate, unpaidExposure,
criticalItems, highItems, daysToStockout, recommendations,

// Assistant
typeMessage, send, thinking, clearChat, suggestions,
modelInfo, contextWindow,

// Settings
dangerZone, deleteAccount, timezone, currency, businessType,
notificationEmail, notificationSms,
```

### 1.2 — Page-by-page bilingual conversion

**Orders page** (`orders/page.tsx`):
- Replace all `STATUS_OPTIONS` label strings with `t("statusPending")` etc.
- Replace `PAYMENT_OPTIONS` labels with `t("payUnpaid")` etc.
- Replace `QUICK_FILTERS` labels
- Header: `t("orderMgmt")`, `t("newOrder")`
- Pagination: `t("prev")`, `t("next")`
- Search placeholder: `t("searchOrders")`

**Products page** (`products/page.tsx`):
- `CATEGORIES` → bilingual category map (Bangla name + English translation)
- Header, search, view toggle labels
- Delete confirmation via `t("deleteProduct")`

**Customers page** (`customers/page.tsx`):
- `SOURCE_OPTIONS` → use t() for each source label
- Schema error messages bilingual
- Header, search, form labels

**Inventory page** (`inventory/page.tsx`):
- Tab labels, stat card labels, action buttons
- Alert messages: `t("noAlerts")`, `t("allStockAdequate")`
- Adjustment form labels

**Assistant page** (`assistant/page.tsx`):
- Conversation sidebar labels
- Empty state copy
- `confirm()` dialogs → native `t()` strings

**Settings page** (`settings/page.tsx`):
- All section headers, field labels, button text

### 1.3 — Shared components

**OrderCard** — status badge labels via t()
**StatusBadge** — map status values to t() keys
**CustomerCard** — all metadata labels
**ProductTable / ProductCard** — column headers, badges
**InventoryTable** — column headers, urgency labels
**ChatMessage** — role labels, timestamp format by lang
**AdjustmentForm** — all field labels

---

## Phase 2 — AI Assistant Upgrade

**Goal:** The AI assistant feels like talking to an expert analyst who knows your business. Context memory across messages. Rich product/inventory/customer insights.

### 2.1 — Context memory in package engine

Current: every call to `package_engine.py` is stateless — it ignores `history`.

Fix: parse `history` (list of LangChain messages) in `generate_smart_response()`:

```python
async def generate_smart_response(
    merchant, user_message, db, history=None
):
    # Extract last 3 assistant responses as context hints
    context = _extract_context(history or [])
    # Use context to detect follow-up questions
    # e.g., "give me more" after a top-products response → expand limit
    intent = detect_intent(user_message, context=context)
```

Add `_extract_context()` that reads the last N AIMessage items to detect:
- Follow-up patterns ("আরো দেখাও", "more details", "explain that")
- Entity references ("which one?", "ওটার স্টক কত?") → resolve from previous response

### 2.2 — Richer response builders

Add to `package_engine.py`:

**Product deep-dive** (triggered by product name in message):
```
rapidfuzz.process.extractOne(message, product_names) → match
→ query that product's variants, stock, sales velocity, revenue
→ "পণ্য X-এর ৩ ভ্যারিয়েন্ট আছে। গত ৩০ দিনে ৪৫টি বিক্রিত। স্টক ১২টি (৮ দিনের মজুদ)।"
```

**Customer profile** (triggered by customer name/phone):
```
fuzzy match customer name → query orders, total spend, last order date
→ "Rahim Khan: ৭টি অর্ডার, মোট ব্যয় ৳৪২,৫০০। শেষ অর্ডার ৩ দিন আগে।"
```

**Order lookup** (triggered by order number):
```
→ fetch order with items, status timeline, payment
```

**Comparative analysis**:
```
"last month vs this month" → _compare_periods() using 60d window split
```

### 2.3 — Suggestion chips in UI

After every AI response, show 3 quick-follow-up chips:

```
[📦 Stock check] [🏆 Top products] [📊 Revenue this month]
```

Chips are context-aware — after a stock response, show restock-related chips.

### 2.4 — Premium Assistant page redesign

Replace basic card layout with:
- Full-height two-panel layout
- Left panel: conversation list with search
- Right panel: chat with glassmorphism bubbles
- Suggestion chips row above input
- Agent indicator (Package AI / Gemini / Claude) in header
- Token/context indicator

---

## Phase 3 — Strengthen Strategic Agents

### 3.1 — Credit Readiness Agent (new)

**File:** `apps/api/app/ai/strategic_agents/credit_readiness.py`

**Purpose:** Estimate how "bankable" this merchant is — useful for BNPL, working capital loans, or premium tier unlocks.

**Score:** 0–100 (higher = more credit-ready)

**Signals:**
| Signal | Weight | Logic |
|--------|--------|-------|
| Revenue consistency | +20 | Last 3 months, low CV (coeff. of variation) |
| Revenue growth | +15 | Positive MoM for 2+ consecutive months |
| Order volume | +15 | ≥50 orders/month = mature |
| Payment collection rate | +15 | paid_orders / total_orders |
| Cancellation rate | −15 | > 30% → penalty |
| Customer diversity | +10 | top customer < 30% of revenue |
| Inventory health | +10 | < 10% SKUs out-of-stock |

**Output:**
```python
@dataclass
class CreditResult:
    credit_score: int
    eligibility: str        # ELIGIBLE | BORDERLINE | NOT_ELIGIBLE
    revenue_consistency: float    # coefficient of variation (lower = better)
    payment_collection_rate: float
    monthly_revenue_avg: float
    credit_limit_estimate: float  # rough: avg_monthly_rev × eligibility_multiplier
    improvement_tips: list[str]
    explanation_bn: str
    explanation_en: str
    details: dict
```

**Credit limit estimate logic:**
```python
multiplier = 1.5 if score >= 75 else 1.0 if score >= 55 else 0.5
credit_limit_estimate = avg_monthly_revenue * multiplier
```

### 3.2 — Enhance existing agents

**TrustGraph enhancements:**
- Add `delivery_speed_score`: avg days from order to delivery
- Add `dispute_rate`: returned / delivered ratio
- Weight score bands more granularly (10-point increments)

**FraudSentinel enhancements:**
- Add `late_night_order_ratio`: orders 11pm–5am as % of total
- Add `single_item_high_value_ratio`: orders with 1 item > ৳5,000 COD
- Add `new_address_spike`: % of orders with unique delivery addresses

**DemandOracle enhancements:**
- Add `seasonal_factor`: compare current month velocity vs same month last year
- Return `suggested_restock_quantity`: velocity × 14 days (2-week buffer)

### 3.3 — AI Center UI — 5-agent tabs

Expand `ai-center/page.tsx` tabs from 3 to 6:

```
[Trust Graph] [Fraud Sentinel] [Growth Coach] [Margin Guardian] [Demand Oracle] [Credit Readiness]
```

Each new tab follows same pattern as Trust tab:
- Score card (number + gauge/meter)
- Details card (flags, recommendations, metrics)
- Explanations in Bangla + English

**Demand Oracle tab specifics:**
- Show critical/high items in a table with columns: Product | Variant | Stock | Velocity/day | Days Left | Urgency
- Color-coded urgency badges (red=CRITICAL, amber=HIGH, yellow=MEDIUM)

**Growth Coach tab specifics:**
- Revenue comparison bar (last 30d vs prev 30d)
- Trend arrow icon
- Recommendations as action chips

**Margin Guardian tab specifics:**
- COD ratio donut (small)
- Unpaid exposure highlighted in amber/red if high

**Credit Readiness tab specifics:**
- Eligibility badge (ELIGIBLE = green, BORDERLINE = amber, NOT_ELIGIBLE = red)
- Credit limit estimate displayed prominently
- Improvement tips as numbered list

---

## Phase 4 — Premium UI for Remaining Pages

**Reference:** Amazon (information density) + Shopify (clean forms) + Linear (keyboard shortcuts, empty states) + modern SaaS (glassmorphism, animations).

### 4.1 — Orders page (highest priority)

**Problems today:** Hardcoded Bangla, no premium styling, card-based layout loses density.

**Target:**
```
┌─ Header ─────────────────────────────────────────────────┐
│ Orders                          [New Order] [Export]      │
│ 3 total · ৳124,500 revenue                               │
├─ Quick filters ──────────────────────────────────────────┤
│ [All] [Pending 12] [Delivered 45] [Cancelled 3]          │
├─ Search + Status + Payment ──────────────────────────────┤
│ [Search orders...] [Status ▼] [Payment ▼] [Date range ▼] │
├─ Table (premium) ────────────────────────────────────────┤
│ # │ Customer │ Items │ Amount │ Payment │ Status │ Date  │
│ ──┼──────────┼───────┼────────┼─────────┼────────┼────── │
│   row with hover effect, status badge, action menu       │
└──────────────────────────────────────────────────────────┘
```

Key upgrades:
- Switch from OrderCard grid → proper `<Table>` component (sortable columns)
- Inline status update dropdown per row
- Revenue summary in header (total revenue for filtered set)
- Date range picker (today / this week / this month / custom)
- Keyboard shortcut: `N` = new order, `F` = focus search
- Bulk select → bulk status update

### 4.2 — Products page

**Target:**
```
┌─ Header ──────────────────────────────────────────────────┐
│ Products (42)               [Grid] [Table] [New Product]  │
│ ৳2.4M total inventory value                               │
├─ Filters ─────────────────────────────────────────────────┤
│ [Search] [Category ▼] [Stock ▼] [Sort: Revenue ▼]        │
├─ Table mode ──────────────────────────────────────────────┤
│ Product │ Category │ Variants │ Stock │ Revenue │ Actions │
└───────────────────────────────────────────────────────────┘
```

Upgrades:
- Total inventory value KPI in header
- Low-stock indicator pill on each product row
- Inline quick-edit for price
- Category filter with icons

### 4.3 — Customers page

**Target:**
```
┌─ Header ──────────────────────────────────────────────────┐
│ Customers (148)         [New Customer] [Import CSV]       │
│ ৳8.2M total lifetime value · 34% retention               │
├─ Segments ────────────────────────────────────────────────┤
│ [All] [VIP] [At Risk] [New (30d)] [Churned]              │
├─ Table ───────────────────────────────────────────────────┤
│ Name │ Phone │ Orders │ LTV │ Last Order │ Source │ Tag  │
└───────────────────────────────────────────────────────────┘
```

Upgrades:
- Customer segments (VIP = LTV > threshold, At Risk = no order 60d, New = created last 30d)
- Lifetime value column
- Tag/label chips (VIP, Regular, Wholesale)
- One-click WhatsApp link from phone number

### 4.4 — Inventory page

**Target:**
```
┌─ Summary cards ───────────────────────────────────────────┐
│ [Total SKUs: 84] [Critical: 3] [Low Stock: 12] [Healthy] │
├─ Tabs: [All] [Critical] [Low Stock] [Out of Stock]        │
├─ Table ───────────────────────────────────────────────────┤
│ Product │ Variant │ Stock │ Velocity │ Days Left │ Action  │
│         │         │ ████░ │  2.3/day │   6 days  │ Restock │
└───────────────────────────────────────────────────────────┘
```

Upgrades:
- Velocity column (units sold per day from DemandOracle logic)
- Days-left column with color coding
- Progress bar for stock level
- Inline restock action (opens adjustment form pre-filled)

### 4.5 — Assistant page (premium redesign)

**Target:**
```
┌─ Sidebar (280px) ─────┬─ Chat area ──────────────────────┐
│ AI Assistant           │  ┌─ Chat header ──────────────┐  │
│ [New Chat]             │  │ SellerMate AI · Package AI  │  │
│ ─────────────          │  └────────────────────────────┘  │
│ Today                  │                                   │
│ ● Stock check           │   [bubble] [bubble] [bubble]     │
│ ● Revenue Q             │                                   │
│ Yesterday              │  ┌─ Suggestions ──────────────┐  │
│ ● Top products          │  │ [Low stock?] [Revenue?]    │  │
│                         │  └────────────────────────────┘  │
│                         │  ┌─ Input ────────────────────┐  │
│                         │  │ Type your question...   [→] │  │
│                         │  └────────────────────────────┘  │
└─────────────────────────┴───────────────────────────────────┘
```

Key features:
- Grouped conversations (Today / Yesterday / This week)
- Glassmorphism chat bubbles (user = primary gradient, AI = glass-card)
- Streaming text animation (letter-by-letter reveal)
- Suggestion chips that trigger canned queries
- Model indicator (which AI engine is active)
- Message timestamp on hover

### 4.6 — Settings page

Upgrade to tabbed settings:
```
[Profile] [Business] [Notifications] [Security] [Integrations]
```

---

## Phase 5 — Advanced Commerce Features

These are post-roadmap features that logically follow. Define them now to avoid architecture conflicts.

### 5.1 — Demand Forecast Page (`/forecast`)
- Dedicated page surfacing DemandOracle results
- Table: all SKUs sorted by urgency
- Restock planner: click → auto-fill adjustment form

### 5.2 — Credit Dashboard (`/credit`)
- Full Credit Readiness breakdown
- Historical score trend (run agents → scores accumulate)
- Tips to improve score

### 5.3 — WhatsApp Integration
- `webhooks.py` already exists
- Connect to WhatsApp Business API
- Auto-create orders from WA messages (existing WHATSAPP channel)

### 5.4 — CSV Export
- Orders export: `/orders?export=csv`
- Customer export: `/customers?export=csv`
- Inventory export

### 5.5 — Push Notifications (web)
- Low stock alerts
- New order notifications
- Daily summary

---

## Execution Plan

### Sprint 1 — Bilingual Completion (3–4 days)

| Day | Work |
|-----|------|
| 1 | Expand i18n.ts with all missing keys |
| 1 | Convert Orders page + OrderCard + StatusBadge |
| 2 | Convert Products page + ProductTable + ProductCard |
| 2 | Convert Customers page + CustomerCard |
| 3 | Convert Inventory page + InventoryTable |
| 3 | Convert Assistant page + ChatMessage + ChatWindow |
| 4 | Convert Settings page + all forms |
| 4 | QA: toggle language on every page, verify all strings switch |

**Definition of done:** Switch language toggle → every visible string changes. No hardcoded Bangla outside i18n.ts.

### Sprint 2 — AI Assistant Upgrade (2–3 days)

| Day | Work |
|-----|------|
| 1 | Add context memory to package_engine.py (parse history) |
| 1 | Add product deep-dive intent (fuzzy product name matching) |
| 2 | Add customer profile intent (fuzzy customer name matching) |
| 2 | Add suggestion chips to ChatWindow component |
| 3 | Premium Assistant page redesign |

### Sprint 3 — Credit Readiness Agent (1–2 days)

| Day | Work |
|-----|------|
| 1 | Write credit_readiness.py |
| 1 | Update strategic_service.py (run 6 agents) |
| 1 | Add CreditReadinessOut schema |
| 2 | Add Credit Readiness tab to AI Center page |
| 2 | Enhance existing agents (delivery speed, late-night orders) |

### Sprint 4 — Premium UI Remaining Pages (3–4 days)

| Day | Work |
|-----|------|
| 1 | Orders page: table layout, date range filter, inline status update |
| 2 | Products page: inventory value KPI, inline edit, premium table |
| 3 | Customers page: segments, LTV column, WA quick-link |
| 3 | Inventory page: velocity column, days-left, progress bar |
| 4 | Assistant page: premium redesign, suggestion chips |
| 4 | Settings page: tabbed layout |

---

## File Change Map

```
apps/web/src/lib/i18n.ts              ← Expand translations
apps/web/src/app/(dashboard)/
  orders/page.tsx                     ← Bilingual + table UI
  products/page.tsx                   ← Bilingual + premium
  customers/page.tsx                  ← Bilingual + segments
  inventory/page.tsx                  ← Bilingual + velocity
  assistant/page.tsx                  ← Bilingual + premium UI
  settings/page.tsx                   ← Bilingual + tabs
  ai-center/page.tsx                  ← 6 agent tabs

apps/web/src/components/
  orders/OrderCard.tsx                ← Bilingual
  orders/StatusBadge.tsx              ← Bilingual
  products/ProductTable.tsx           ← Bilingual
  products/ProductCard.tsx            ← Bilingual
  customers/CustomerCard.tsx          ← Bilingual
  inventory/InventoryTable.tsx        ← Bilingual + velocity
  assistant/ChatWindow.tsx            ← Premium + suggestions
  assistant/ChatMessage.tsx           ← Premium bubbles

apps/api/app/ai/
  package_engine.py                   ← Context memory
  strategic_agents/
    credit_readiness.py               ← NEW
    trust_graph.py                    ← Enhanced
    fraud_sentinel.py                 ← Enhanced
    demand_oracle.py                  ← Seasonal factor
    __init__.py                       ← Export CreditReadiness

apps/api/app/schemas/strategic.py     ← CreditReadinessOut
apps/api/app/services/strategic_service.py  ← Run 6 agents
```

---

## Quality Standards

### Every page must:
- [ ] Work in both Bangla and English (language toggle test)
- [ ] Work in dark and light mode
- [ ] Be responsive (320px mobile → 1920px desktop)
- [ ] Show loading skeleton while fetching
- [ ] Show meaningful empty state when no data
- [ ] Show error state with retry option

### Every AI response must:
- [ ] Pull real numbers from the database
- [ ] Never say "I don't know" without offering alternatives
- [ ] Match the language of the question (Bangla question → Bangla answer)
- [ ] Complete in < 2 seconds on the package engine

### Every agent score must:
- [ ] Be 0–100 with documented scoring formula
- [ ] Include explanation in both Bangla and English
- [ ] Store in strategic_insights table (so history accumulates)
- [ ] Update when "Run Agents" is clicked

---

## Design Tokens Reference

```css
/* Key CSS variables (already in globals.css) */
--background: 220 20% 97%      /* light */
--background: 222 47% 5%       /* dark */
--primary: 226 76% 52%         /* indigo-blue */

/* Premium utility classes */
.glass-card     → glassmorphism base
.gradient-primary → blue→indigo→violet gradient
.gradient-text  → same as text clip
.stat-card-blue/violet/emerald/amber → tinted backgrounds
.animate-slide-up / .animate-fade-in / .animate-scale-in
.bg-grid        → subtle dot grid background
```

---

*This roadmap defines the full engineering scope for SellerMate Commerce OS v2. Each sprint is independently shippable. Start with Sprint 1 (bilingual) as it unblocks all subsequent work.*
