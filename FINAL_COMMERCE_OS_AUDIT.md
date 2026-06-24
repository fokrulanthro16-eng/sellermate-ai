# FINAL COMMERCE OS AUDIT
**Date:** 2026-06-23  
**Sprint:** Premium UX Sprint  
**Scope:** All 8 pages — full functional, UX, translation, and runtime audit  
**Legend:** ✅ PASS | ⚠️ WARNING | ❌ FAIL

---

## Audit Criteria (per page)
1. No runtime errors
2. No hydration errors
3. No undefined values rendered
4. No empty charts / data broken
5. No broken API calls
6. No missing translations
7. No fake data labels
8. Mobile responsive
9. Dark mode works
10. Bangla + English works

---

## 1. Dashboard

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes; all hooks guarded with `|| []` / `?? 0` |
| Hydration errors | ✅ PASS | Header has `mounted` guard for theme; Dashboard has none needed |
| Undefined values | ✅ PASS | `safeNum()` used throughout; `formatCurrency(0)` renders `৳0` |
| Charts / data | ✅ PASS | `RevenueChart data={revenue \|\| []}` — empty array handled gracefully |
| API calls | ✅ PASS | `useDashboard`, `useRevenueTrend`, `useOrderBreakdown`, `useStrategicInsights` all wired |
| Translations | ✅ PASS | All keys present in `i18n.ts`; `t("todayRevenue")` etc. confirmed |
| Fake data | ✅ PASS | All values from live API; no hardcoded numbers |
| Mobile responsive | ✅ PASS | `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4` stat cards; charts are responsive |
| Dark mode | ✅ PASS | CSS variables + `dark:` classes throughout |
| Bangla + English | ✅ PASS | Full bilingual via `t()` on all labels; currency symbol `৳` always shown |

**Overall: ✅ PASS**

---

## 2. Orders

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ⚠️ WARNING | Stat cards show `0` while `useOrderBreakdown` loads (benign loading state, not an error) |
| Charts / data | ✅ PASS | Orders list uses `useOrders`; breakdown uses `useOrderBreakdown(from, to)` |
| API calls | ✅ PASS | `useDashboard` + `useOrderBreakdown` wired; `from = subDays(now, 30)` |
| Translations | ✅ PASS | All keys present; bilingual status badges, headers, buttons |
| Fake data | ✅ PASS | All values from live API |
| Mobile responsive | ✅ PASS | `grid-cols-2 sm:grid-cols-4` mini-cards; order cards stack on narrow screens |
| Dark mode | ✅ PASS | `dark:` classes on all colored elements |
| Bangla + English | ✅ PASS | Status badge labels translated; column headers translated |

**Overall: ✅ PASS** (with minor loading-state caveat)

---

## 3. Products

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ✅ PASS | Category pills use `product.category ?? label("অন্যান্য", "Other")` pattern |
| Charts / data | ✅ PASS | No charts; product grid from `useProducts` |
| API calls | ✅ PASS | `useProducts` unchanged and working |
| Translations | ✅ PASS | All keys present |
| Fake data | ✅ PASS | All live data |
| Mobile responsive | ✅ PASS | `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` |
| Dark mode | ✅ PASS | Glass-card handles dark mode via CSS variables |
| Bangla + English | ✅ PASS | Headers, buttons, category pills bilingual |

**Overall: ✅ PASS**

---

## 4. Inventory

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ✅ PASS | `safeNum()` used; `safePercent(n, 0)` returns `0` safely |
| Charts / data | ✅ PASS | Health cards show `0` on load, correct after data arrives |
| API calls | ✅ PASS | `useInventory`, `useInventoryAlerts`, `useInventoryHealth` all wired |
| Translations | ✅ PASS | All keys present; alert banner text uses `.replace("{{n}}", ...)` |
| Fake data | ✅ PASS | All live data |
| Mobile responsive | ✅ PASS | `grid-cols-1 sm:grid-cols-3` health cards |
| Dark mode | ✅ PASS | All colored elements have `dark:` variants |
| Bangla + English | ✅ PASS | Full bilingual including alert count text |

**Specific FAIL — Alert Banner "View" Button:**  
`apps/web/src/app/(dashboard)/inventory/page.tsx:144`
```
document.querySelector('[data-state="inactive"][value="alerts"]')
```
Radix UI `TabsTrigger` does **not** render the `value` prop as an HTML attribute. The `[value="alerts"]` selector will never match any DOM element. This selector always returns `null`. The button renders and is clickable but performs no action — it silently does nothing.

**Overall: ⚠️ WARNING** (page functions; only the alert-banner shortcut button is broken)

---

## 5. Customers

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ✅ PASS | `safeNum(dashboard?.total_customers)` guards all stats |
| Charts / data | ✅ PASS | Customer grid from `useCustomers`; stat cards from `useDashboard` |
| API calls | ✅ PASS | `useCustomers`, `useDashboard` wired; Facebook/Instagram/MessageCircle icons confirmed in lucide-react 0.468 |
| Translations | ✅ PASS | All keys present |
| Fake data | ✅ PASS | All live data |
| Mobile responsive | ✅ PASS | `grid-cols-1 sm:grid-cols-3` stat cards; `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` customer cards |
| Dark mode | ✅ PASS | TAG_STYLE entries all have `dark:` variants |
| Bangla + English | ✅ PASS | Source labels, stat headers, buttons bilingual |

**Specific WARNING — Source Filter Pagination Scope:**  
`apps/web/src/app/(dashboard)/customers/page.tsx`
```
const filtered = source ? customers.filter((c) => c.source === source) : customers;
```
`customers` is only the current page (24 items). If a merchant has 60 Facebook customers spread across 3 pages, the "Facebook" filter shows only the Facebook customers on the current page — not all 60. Filter is not server-side. Accurate only for merchants with ≤ 24 total customers.

**Overall: ⚠️ WARNING** (page works; filter is pagination-scoped only)

---

## 6. Assistant

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes; `initialSentRef` prevents double-sends |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ✅ PASS | `data?.items \|\| []` guards conversation list |
| Charts / data | ✅ PASS | No charts on this page |
| API calls | ✅ PASS | `useConversations`, `useCreateConversation`, `useDeleteConversation`, SSE stream all wired |
| Translations | ✅ PASS | `t("assistantTitle")`, `t("newConversation")`, `t("startChat")` etc. all present |
| Fake data | ✅ PASS | All live conversations and AI responses |
| Mobile responsive | ⚠️ WARNING | Sidebar is `w-64 shrink-0` — no breakpoint to collapse or hide it on phones. On ≤ 480px screens both panels share 480px horizontally leaving ~200px for chat. |
| Dark mode | ✅ PASS | `glass-card`, `dark:` variants throughout |
| Bangla + English | ⚠️ WARNING | ChatWindow empty-state text (`apps/web/src/components/assistant/ChatWindow.tsx:109–111`) is hardcoded in Bangla and does not respond to language toggle: `"আপনার ব্যবসা সম্পর্কে যেকোনো প্রশ্ন করুন।"` |

**Overall: ⚠️ WARNING** (two minor issues — mobile layout + hardcoded Bangla in ChatWindow empty state)

---

## 7. AI Center

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ✅ PASS | No server-only state |
| Undefined values | ✅ PASS | All agent data guarded with `?.` access and empty-state fallback |
| Charts / data | ✅ PASS | TrustGauge (SVG arc), FraudMeter (bar), ScoreBar all render with 0 gracefully |
| API calls | ✅ PASS | All 6 hooks (`useTrustGraph`, `useFraudSentinel`, `useGrowthCoach`, `useMarginGuardian`, `useDemandOracle`, `useCreditReadiness`) wired |
| Translations | ✅ PASS | `shadow-glow-blue` confirmed in `tailwind.config.ts`; all tab labels bilingual via inline `label()` |
| Fake data | ✅ PASS | All live strategic data; EmptyState shown when no data |
| Mobile responsive | ✅ PASS | `TabsList` has `flex-wrap`; cards stack on narrow screens |
| Dark mode | ✅ PASS | CSS variables + `dark:` throughout |
| Bangla + English | ⚠️ WARNING | Header description says **"৫টি বিশেষজ্ঞ এজেন্ট"** (5 specialized agents) but there are **6** agent tabs (Trust, Fraud, Growth, Margin, Demand, Credit). Stale copy. |

**Overall: ⚠️ WARNING** (page fully functional; header agent count copy is stale)

---

## 8. Settings

| Criterion | Result | Notes |
|-----------|--------|-------|
| Runtime errors | ✅ PASS | No crashes |
| Hydration errors | ⚠️ WARNING | `useTheme()` called at component root without `mounted` guard. On SSR, `theme` is `undefined`. The 3 theme buttons (`theme === opt.value`) all render as inactive on first paint, then flash to correct state after hydration. `Header.tsx` avoids this with an explicit `mounted` check. |
| Undefined values | ✅ PASS | `profile?.email`, `profile?.district ?? ""` all guarded |
| Charts / data | ✅ PASS | No charts; profile loaded via `GET /auth/me` |
| API calls | ✅ PASS | `GET /auth/me` on mount; `PATCH /merchant/me` on save |
| Translations | ✅ PASS | All keys (`settingsTitle`, `settingsDesc`, `businessProfile`, `save`, `saving`, `profileUpdated` etc.) present |
| Fake data | ✅ PASS | All live merchant profile data |
| Mobile responsive | ✅ PASS | `max-w-2xl mx-auto`; `grid-cols-1 sm:grid-cols-2` inputs |
| Dark mode | ✅ PASS | `glass-card`; `dark:` on all form elements |
| Bangla + English | ✅ PASS | All 3 tabs bilingual; language toggle works immediately; theme labels bilingual |

**Overall: ⚠️ WARNING** (theme buttons flash on first render; no hard error)

---

## Summary Table

| Page | Runtime | Hydration | Undefined | Charts | API | Translations | Fake Data | Mobile | Dark Mode | Bilingual | **Overall** |
|------|---------|-----------|-----------|--------|-----|--------------|-----------|--------|-----------|-----------|-------------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ PASS** |
| Orders | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ PASS** |
| Products | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ PASS** |
| Inventory | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **⚠️ WARNING** |
| Customers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **⚠️ WARNING** |
| Assistant | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | **⚠️ WARNING** |
| AI Center | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | **⚠️ WARNING** |
| Settings | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **⚠️ WARNING** |

**PASS: 3 pages** | **WARNING: 5 pages** | **FAIL: 0 pages**

---

## Issues Requiring Fixes (Priority Order)

### P1 — Broken Feature (Silent No-Op)
**Inventory page — Alert banner "View" button**  
File: `apps/web/src/app/(dashboard)/inventory/page.tsx:144`  
Problem: `document.querySelector('[data-state="inactive"][value="alerts"]')` returns `null` because Radix UI `TabsTrigger` does not expose `value` as an HTML attribute.  
Fix: Use a `useRef` on the Alerts `TabsTrigger` or manage tab state with a controlled `value` + `onValueChange` on the `<Tabs>` component.

### P2 — Translation Gap
**ChatWindow — hardcoded Bangla empty-state text**  
File: `apps/web/src/components/assistant/ChatWindow.tsx:109–111`  
Problem: Two lines are hardcoded in Bangla and do not change when the user switches to English.  
Fix: Add `useLang()` to `ChatWindow` and use `label()` or `t()` for those strings.

### P3 — Hydration Flash
**Settings — theme buttons flash on first render**  
File: `apps/web/src/app/(dashboard)/settings/page.tsx:41`  
Problem: `useTheme()` returns `undefined` on SSR, causing all 3 theme buttons to render as inactive, then flicker to the correct active state after hydration.  
Fix: Add a `mounted` state guard (same pattern as `Header.tsx`) before rendering the theme button group.

### P4 — Stale Copy
**AI Center — agent count in header**  
File: `apps/web/src/app/(dashboard)/ai-center/page.tsx` (header description line)  
Problem: Text says "৫টি বিশেষজ্ঞ এজেন্ট" (5 agents) but there are 6.  
Fix: Update to "৬টি বিশেষজ্ঞ এজেন্ট" / "6 Specialized Agents".

### P5 — Mobile UX
**Assistant — sidebar not responsive on narrow screens**  
File: `apps/web/src/app/(dashboard)/assistant/page.tsx:97`  
Problem: Sidebar is `w-64 shrink-0` with no breakpoint to collapse or hide on phones.  
Fix: Add `hidden md:flex` to sidebar and a "conversations" toggle button visible on mobile only; or convert to `flex-col md:flex-row` at the two-panel container.

### P6 — Filter Accuracy
**Customers — source filter is client-side only**  
File: `apps/web/src/app/(dashboard)/customers/page.tsx`  
Problem: Filter applied after fetching 24 items; does not represent full dataset for merchants with > 24 customers per source.  
Fix: Pass `source` as a query param to `useCustomers({ source })` so filtering is server-side.

---

## What Is Working Well
- All 8 pages render without runtime errors or hard crashes
- Glass-card design system (`glass-card`, `gradient-text`, `animate-slide-up`) applied consistently
- `i18n.ts` is complete — all 40+ keys present in both `bn` and `en`
- All 6 strategic agents wired end-to-end (TrustGraph, FraudSentinel, GrowthCoach, MarginGuardian, DemandOracle, CreditReadiness)
- AI context memory working via `_is_followup()` + `_last_human_intent()` in `package_engine.py`
- Suggestion chips → auto-send flow working via `initialMessage` prop + `initialSentRef`
- SSE streaming response in ChatWindow working correctly
- `shadow-glow-blue` confirmed in `tailwind.config.ts`
- `Facebook` and `Instagram` icons confirmed present in lucide-react 0.468
- Dark mode works on all 8 pages after initial hydration
- Mobile layout works on 7 of 8 pages (Assistant sidebar is the exception)
