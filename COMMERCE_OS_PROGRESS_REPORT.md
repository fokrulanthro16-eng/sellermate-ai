# SellerMate Commerce OS — Progress Report

> Generated: 2026-06-23 | Sprint: Bilingual + AI Agents + Credit Readiness

---

## Overall Status: 6/7 Roadmap Items Complete

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Complete bilingual support | ✅ Done | All 6 pages wired to useLang() |
| 2 | Strengthen AI Assistant | ✅ Done | Package engine + real DB |
| 3 | Demand Oracle | ✅ Done | velocity, days-to-stockout, urgency |
| 4 | Margin Guardian | ✅ Done | COD, refund, discount, unpaid exposure |
| 5 | Growth Coach | ✅ Done | MoM trend, polyfit slope, retention |
| 6 | Credit Readiness | ✅ Done | 7-signal scoring, credit limit estimate |
| 7 | Premium E-commerce UI | 🔶 Partial | Dashboard/Analytics/AI Center done; Orders/Products/Customers/Inventory/Assistant basic |

---

## Sprint Completions

### Bilingual Support — Sprint 1 ✅

All pages now use `useLang()` / `t()`. No hardcoded Bangla strings remain in page components.

| Page | Before | After |
|------|--------|-------|
| `orders/page.tsx` | Hardcoded Bangla | ✅ `t("statusPending")`, `t("orderMgmt")` etc. |
| `customers/page.tsx` | Hardcoded Bangla | ✅ `t("sourceFacebook")`, `t("nameRequired")` etc. |
| `products/page.tsx` | Hardcoded categories array | ✅ Bilingual `CATEGORY_MAP` with `lang === "en"` display |
| `inventory/page.tsx` | Hardcoded Bangla | ✅ `t("monitorStock")`, `t("lowStockBanner")` etc. |
| `assistant/page.tsx` | Hardcoded Bangla | ✅ `t("startChatPrompt")`, `t("selectOrNewChat")` etc. |
| `settings/page.tsx` | Hardcoded Bangla | ✅ `t("settingsTitle")`, `t("businessProfile")` etc. |

**i18n.ts additions:** 40+ new keys across Orders, Customers, Products, Inventory, Assistant sections.

New keys include:
- `statusPending/Confirmed/Processing/Shipped/Delivered/Cancelled/Returned`
- `statusUnpaid/Partial/Paid/Refunded`
- `sourceFacebook/Whatsapp/Instagram/Manual/WalkIn`
- `filterAll`, `searchOrders`, `monitorStock`, `lowStockBanner`
- `startChatPrompt`, `selectOrNewChat`, `startChatPrompt`
- `clearFilters`, `totalProducts`, `manageCatalog`, `addProduct`

---

### Credit Readiness Agent — Sprint 3 ✅

**File:** `apps/api/app/ai/strategic_agents/credit_readiness.py`

**Algorithm:** 7 signals → 0-100 score → ELIGIBLE / BORDERLINE / NOT_ELIGIBLE

| Signal | Max Points | Logic |
|--------|-----------|-------|
| Revenue consistency (CV ≤ 0.15) | +20 | Coefficient of variation on 3-month buckets |
| Revenue growth (2+ consecutive MoM) | +15 | numpy or pure-Python slope |
| Order volume (≥ 50/month) | +15 | avg over 90-day window |
| Payment collection rate (≥ 85%) | +15 | paid / total orders |
| Cancellation penalty (> 30%) | −15 | flagged as REDUCE_CANCELLATIONS |
| Customer diversity (top < 30%) | +10 | top customer revenue share |
| Inventory health (< 10% OOS) | +10 | joins ProductVariant → Product |

**Credit limit estimate:**
```
ELIGIBLE    → monthly_avg × 1.5
BORDERLINE  → monthly_avg × 1.0
NOT_ELIGIBLE → monthly_avg × 0.5
```

**Improvement tips (localized):**
- STABILIZE_REVENUE, GROW_REVENUE, INCREASE_ORDER_VOLUME
- IMPROVE_PAYMENT_COLLECTION, REDUCE_CANCELLATIONS
- DIVERSIFY_CUSTOMER_BASE, RESTOCK_INVENTORY

**Wiring completed:**
- `__init__.py` — exports `CreditReadiness`, `CreditResult`
- `schemas/strategic.py` — added `CreditReadinessOut`, `StrategicRunResult.credit` field
- `strategic_service.py` — runs 6 agents, saves 6 insights per `/run` call
- `useStrategic.ts` — added `useCreditReadiness()` hook
- `ai-center/page.tsx` — 6th tab (Credit Readiness) with eligibility badge + tips

---

### AI Center — 6 Agent Tabs ✅

Tab layout expanded from 3 → 6 tabs:

```
[Trust Graph] [Fraud Sentinel] [Growth Coach] [Margin Guardian] [Demand Oracle] [Credit Readiness]
```

Summary row: 6 score cards with color-coded borders (emerald / orange / blue / violet / amber / indigo).

**Strategic service now runs all 6 agents** and stores full payload (not just `details`) for all new agents:
- growth_coach: `trend_direction`, `revenue_growth_pct`, `retention_rate`, `recommendations`, `explanation_bn/en`
- margin_guardian: `risk_level`, `cod_ratio`, `refund_rate`, `flags`, `explanation_bn/en`
- demand_oracle: `restock_score`, `critical_count`, `high_count`, `critical_items[]`, `explanation_bn/en`
- credit_readiness: `eligibility`, `credit_limit_estimate`, `improvement_tips[]`, `explanation_bn/en`

---

## File Change Map

### Backend (Python / FastAPI)

| File | Change |
|------|--------|
| `app/ai/strategic_agents/credit_readiness.py` | NEW — 6-signal credit scoring agent |
| `app/ai/strategic_agents/__init__.py` | Added CreditReadiness + CreditResult exports |
| `app/schemas/strategic.py` | Added CreditReadinessOut; added `credit` field to StrategicRunResult |
| `app/services/strategic_service.py` | Runs 6 agents; full payload storage for growth/margin/demand/credit |

### Frontend (Next.js / TypeScript)

| File | Change |
|------|--------|
| `src/lib/i18n.ts` | +40 translation keys (orders/customers/products/inventory/assistant) |
| `src/app/(dashboard)/orders/page.tsx` | Full bilingual (STATUS, PAYMENT, QUICK_FILTER via t()) |
| `src/app/(dashboard)/customers/page.tsx` | Full bilingual (SOURCE_OPTIONS, form labels, validation msgs) |
| `src/app/(dashboard)/products/page.tsx` | Full bilingual (CATEGORY_MAP with bn/en display) |
| `src/app/(dashboard)/inventory/page.tsx` | Full bilingual (health cards, alert banner, tabs) |
| `src/app/(dashboard)/assistant/page.tsx` | Full bilingual (conversation list, empty state, buttons) |
| `src/app/(dashboard)/settings/page.tsx` | Full bilingual (profile form, security section) |
| `src/app/(dashboard)/ai-center/page.tsx` | 6 agent tabs; Credit Readiness tab with eligibility badge |
| `src/hooks/useStrategic.ts` | Added useGrowthCoach, useMarginGuardian, useDemandOracle, useCreditReadiness |

---

## Architecture: 6-Agent Intelligence Layer

```
/ai/strategic/run
      │
      ├── TrustGraph        → delivery rate, payment rate, retention
      ├── FraudSentinel     → cancellation spike, stale unpaid, order spike
      ├── GrowthCoach       → revenue trend (numpy polyfit), MoM, concentration
      ├── MarginGuardian    → COD ratio, refund rate, discount depth, exposure
      ├── DemandOracle      → velocity per SKU, days-to-stockout, urgency
      └── CreditReadiness   → 7-signal scoring, credit limit estimate
             │
             └── All 6 saved to strategic_insights table
                 agent_name: trust_graph | fraud_sentinel | growth_coach
                             margin_guardian | demand_oracle | credit_readiness
```

---

## Remaining Work (Roadmap Items)

### Premium UI — 6 Pages Remaining

These pages use correct bilingual strings but still use the basic card/table UI from the original codebase. The premium glassmorphism treatment (applied to Dashboard, Analytics, AI Center) has not yet been applied to:

1. **Orders page** — needs table layout, date range filter, inline status update
2. **Products page** — needs inventory value KPI, low-stock indicator, inline edit
3. **Customers page** — needs segments (VIP/At Risk/New/Churned), LTV column
4. **Inventory page** — needs velocity column, days-left progress bars
5. **Assistant page** — needs premium two-panel layout, suggestion chips, streaming UI
6. **Settings page** — needs tabbed layout (Profile / Security / Notifications)

### AI Assistant Context Memory

The Package Engine currently handles each message independently. Follow-up questions ("আরো দেখাও", "which one?") lose context. Next step: parse `history` parameter in `generate_smart_response()` to detect follow-up intent.

---

## Verification Checklist

| Check | Status |
|-------|--------|
| Backend imports clean (no circular refs) | ✅ Verified |
| ProductVariant queries join through Product | ✅ Fixed (credit_readiness.py) |
| Strategic service runs 6 agents per `/run` | ✅ Wired |
| Full payload stored (not just details) | ✅ Fixed for growth/margin/demand/credit |
| `useStrategic.ts` exports 4 new hooks | ✅ Verified |
| AI Center renders 6 tabs | ✅ Verified |
| All 6 pages use `useLang()` | ✅ Verified |
| i18n.ts has bn+en entries for all new keys | ✅ Verified |
| No hardcoded Bangla in page components | ✅ Verified |
| No mock data — all from real DB | ✅ All agents use SQLAlchemy async queries |
| No external API required | ✅ Package engine only |

---

## No-Change Guarantees

- ✅ No git push performed
- ✅ No deployment triggered
- ✅ No breaking changes to existing API contracts
- ✅ No mock/hardcoded numbers in any agent
- ✅ Existing trust_graph and fraud_sentinel unchanged
- ✅ Package engine (rapidfuzz + numpy) unchanged
- ✅ Gemini routing unchanged (Priority 1 still Gemini if key set)
