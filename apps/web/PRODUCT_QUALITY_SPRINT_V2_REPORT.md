# SellerMate AI — Product Quality Sprint v2 Report

**Date:** 2026-06-23  
**Sprint Goal:** Language system, AI assistant fallback, strategic agent upgrades, premium UI, expanded demo data  
**Build Status:** ✅ 22 routes compiled, 0 TypeScript errors

---

## Phase 1 — Language System (Bangla/English Toggle)

### Files Created
| File | Purpose |
|------|---------|
| `apps/web/src/lib/i18n.ts` | Full translation dictionary — 70+ keys in both bn/en |
| `apps/web/src/contexts/LangContext.tsx` | React context: lang, setLang, t() — localStorage backed |

### Files Modified
| File | Change |
|------|--------|
| `apps/web/src/app/layout.tsx` | Wrapped with `<LangProvider>` |
| `apps/web/src/components/layout/Header.tsx` | Globe icon toggle — clicks between বাং ↔ EN |
| `apps/web/src/components/layout/Sidebar.tsx` | All nav labels use `t(key)` — fully translated |
| `apps/api/app/ai/prompts/system.py` | Replaced "f-commerce" → "ই-কমার্স" |
| `apps/web/src/app/(auth)/login/page.tsx` | Replaced "f-commerce" references |
| `apps/web/src/app/(auth)/register/page.tsx` | Replaced "f-commerce" references |

### Behavior
- Default language: **Bangla** (bn)
- Toggle is a pill button in the Header topbar: `Globe + "EN"` or `"বাং"`
- Persisted to `localStorage` key `sellermate_lang`
- All sidebar nav labels switch on toggle: ড্যাশবোর্ড ↔ Dashboard, অর্ডার ↔ Orders, etc.
- Sidebar logo subtitle now shows from `t("businessOS")` — no more "f-commerce"

---

## Phase 2 — Real AI Assistant Fallback

### Problem
`ANTHROPIC_API_KEY` is empty in `apps/api/.env` → agent.py always crashes with authentication error.

### Solution
Created `apps/api/app/ai/fallback_assistant.py` — a smart local DB fallback.

### File Created
`apps/api/app/ai/fallback_assistant.py`

### Capabilities (no API key needed)
| Intent | Detection | Response |
|--------|-----------|----------|
| Greeting | হ্যালো, hello, hi, salam | Welcome message with feature list |
| Today summary | আজ, today, সারাংশ, overview | Live order count, revenue, pending, stock alerts |
| Stock check | স্টক, stock, inventory, কম স্টক | Low/out-of-stock counts + top 5 low items |
| Orders | অর্ডার, order, বাতিল, cancel | 7 or 30 day report with status breakdown |
| Customers | গ্রাহক, customer, VIP | Total, repeat, VIP counts + retention rate |
| Products | পণ্য, product, টপ, best | Top 5 sold by delivered order quantity |
| Revenue | রাজস্ব, revenue, আয়, income | Revenue + avg order value + top products |
| Strategic | ট্রাস্ট, trust, ফ্রড, fraud | Redirects to AI Center page |
| Help | help, সাহায্য | Full capability list |
| Fallback | anything else | Today summary + suggestion |

### Language Detection
Bangla Unicode range `[ঀ-৿]` → reply in Bengali. Otherwise → reply in English.

### Wired Into Agent
`apps/api/app/ai/agent.py` — checks if `settings.anthropic_api_key` is empty at the top of `run_agent()`. If empty → yields from `stream_fallback()` and returns early. No API call made.

---

## Phase 3 — Strategic Agent Upgrades

### TrustGraph Upgrades (`trust_graph.py`)
New fields added to `TrustResult`:
- `positive_signals: list[str]` — e.g., `["STRONG_DELIVERY_RATE", "HIGH_PAYMENT_COLLECTION"]`
- `explanation_bn: str` — Bengali explanation of the score
- `explanation_en: str` — English explanation

### FraudSentinel Upgrades (`fraud_sentinel.py`)
New fields added to `FraudResult`:
- `risk_level: str` — `LOW | MEDIUM | HIGH | CRITICAL` (derived from score)
- `suspicious_patterns: list[str]` — e.g., `["STALE_UNPAID", "MASS_CANCELLATION"]`
- `explanation_bn: str` — Bengali fraud risk summary
- `explanation_en: str` — English fraud risk summary

### New API Endpoint
`GET /api/v1/ai/strategic/summary`

Returns:
```json
{
  "trust_score": 72,
  "fraud_score": 25,
  "risk_level": "LOW",
  "top_insights": ["ELEVATED_CANCELLATION_RATE", "STRONG_DELIVERY_RATE", "STALE_UNPAID"],
  "explanation_bn": "আপনার ব্যবসার ট্রাস্ট স্কোর চমৎকার...",
  "explanation_en": "Excellent trust score..."
}
```

Schema: `StrategicSummaryOut` added to `schemas/strategic.py`  
Service: `get_summary()` added to `services/strategic_service.py`  
Router: `GET /summary` added to `routers/strategic.py`

---

## Phase 4 — Premium UI Redesign

### Login Page (`/login`)
- Split-panel layout: left brand panel (primary gradient) + right form
- Left panel: animated circles, feature highlights (TrendingUp, Shield, BarChart3)
- Right panel: clean form, taller inputs (h-11), amber demo button
- Footer copyright line

### Register Page (`/register`)
- Matching split-panel: violet→primary gradient + right form
- Left panel: CheckCircle perk list (free account, unlimited, AI analytics)
- Right panel: all fields, h-10 inputs, separator, demo button

---

## Phase 5 — Demo Data Expansion

### Updated Seed: `apps/api/seed_demo_data.py`

| Entity | Before | After |
|--------|--------|-------|
| Products | 25 | **30** |
| Variants | 47 | **60+** |
| Customers | 80 | **100** |
| Orders | ~103 | **~180** |

### 5 New Products Added
1. Men's Polo T-Shirt (পোশাক) — 3 variants
2. Wireless Phone Charger 15W (ইলেকট্রনিক্স) — 2 variants
3. Organic Ghee 500ml (খাদ্যপণ্য) — 2 variants
4. Wall Clock Wooden (গৃহস্থালি) — 2 variants
5. Tasbeeh 99 Beads (ধর্মীয় পণ্য) — 3 variants

### Order Distribution (30 days)
- Spike day (day 8): **20 orders** (fraud signal)
- Stale unpaid threshold: **15 orders** >7 days old, COD, UNPAID
- Status mix: ~42% delivered, ~20% cancelled, ~38% other

---

## Phase 6 — Final QA

### TypeScript Check
```
npx tsc --noEmit → Exit 0 (no type errors)
```

### Production Build
```
npx next build → ✅ 22 routes compiled successfully
```

### Route Table
```
○ /login             ○ /register          ○ /onboarding
○ /dashboard         ○ /products          ○ /products/new
ƒ /products/[id]     ƒ /products/[id]/edit ○ /inventory
○ /inventory/adjustments ○ /orders        ○ /orders/new
ƒ /orders/[id]       ○ /customers         ƒ /customers/[id]
○ /analytics         ○ /assistant         ○ /ai-center
○ /settings
```

---

## Files Modified/Created This Sprint

### Backend
| File | Change |
|------|--------|
| `apps/api/app/ai/fallback_assistant.py` | NEW — smart local DB fallback |
| `apps/api/app/ai/agent.py` | Check empty API key → use fallback |
| `apps/api/app/ai/prompts/system.py` | "f-commerce" → "ই-কমার্স" |
| `apps/api/app/ai/strategic_agents/trust_graph.py` | Added positive_signals, explanation_bn/en |
| `apps/api/app/ai/strategic_agents/fraud_sentinel.py` | Added risk_level, suspicious_patterns, explanation_bn/en |
| `apps/api/app/schemas/strategic.py` | Added StrategicSummaryOut, new fields to existing schemas |
| `apps/api/app/services/strategic_service.py` | Updated run_agents() + added get_summary() |
| `apps/api/app/routers/strategic.py` | Added GET /summary endpoint |
| `apps/api/seed_demo_data.py` | 30p / 60+v / 100c / 180o |

### Frontend
| File | Change |
|------|--------|
| `apps/web/src/lib/i18n.ts` | NEW — 70+ key translation dictionary |
| `apps/web/src/contexts/LangContext.tsx` | NEW — React context with localStorage |
| `apps/web/src/app/layout.tsx` | Wrapped with LangProvider |
| `apps/web/src/components/layout/Header.tsx` | Globe language toggle button |
| `apps/web/src/components/layout/Sidebar.tsx` | All labels use t() translation |
| `apps/web/src/app/(auth)/login/page.tsx` | Premium split-panel redesign |
| `apps/web/src/app/(auth)/register/page.tsx` | Premium split-panel redesign |

---

## Remaining Non-Blockers

| Item | Notes |
|------|-------|
| Anthropic API key | Still empty — fallback works correctly |
| Password change endpoint | Backend not implemented — UI shows "coming soon" |
| WhatsApp integration | Always disconnected — acceptable |
| Re-seed database | Run `python seed_demo_data.py` then `python trigger_agents.py` to refresh demo data |
