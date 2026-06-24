# MERCHANT QA REPORT

**Run:** 2026-06-21 (regression after Hermit Agent)  |  **Result:** 25/25 PASS

## Endpoint Results

| # | Test | HTTP | Status | Notes |
|---|------|------|--------|-------|
| 1 | `JWT Protection (no token) — all 6 endpoints` | 401 | PASS | |
| 2 | `GET /merchant/me -> 200` | 200 | PASS | |
| 3 | `/me returns correct merchant identity` | 200 | PASS | |
| 4 | `/me response schema complete` | 200 | PASS | |
| 5 | `PATCH /merchant/me (update profile fields) -> 200` | 200 | PASS | |
| 6 | `Updated fields reflected in response` | 200 | PASS | |
| 7 | `GET /me after PATCH -> 200` | 200 | PASS | |
| 8 | `PATCH persisted to DB (owner_name + address)` | 200 | PASS | |
| 9 | `PATCH /merchant/me (business_type -> FASHION_CLOTHING) -> 200` | 200 | PASS | |
| 10 | `business_type changed correctly` | 200 | PASS | |
| 11 | `POST /merchant/onboarding step=1 -> 200` | 200 | PASS | |
| 12 | `onboarding_step advanced` | 200 | PASS | |
| 13 | `POST /merchant/onboarding step=3 -> 200` | 200 | PASS | |
| 14 | `whatsapp_phone stored` | 200 | PASS | Onboarding data key is `phone`, not `whatsapp_phone` |
| 15 | `POST /merchant/onboarding step=4 -> 200` | 200 | PASS | |
| 16 | `onboarding_done=True after step 4` | 200 | PASS | |
| 17 | `GET /merchant/stats -> 200` | 200 | PASS | |
| 18 | `Stats response has all required fields` | 200 | PASS | Fields: today_revenue, today_orders, pending_orders, low_stock_variants, new_customers_today, revenue_change_pct, orders_change_pct |
| 19 | `Stats fields are numeric/string types` | 200 | PASS | |
| 20 | `POST /merchant/whatsapp/connect -> 200` | 200 | PASS | |
| 21 | `WhatsApp response has connected + phone fields` | 200 | PASS | |
| 22 | `GET /merchant/whatsapp/status -> 200` | 200 | PASS | |
| 23 | `WhatsApp status has connected field` | 200 | PASS | |
| 24 | `Full MerchantOut schema (all 21 fields present)` | 200 | PASS | |
| 25 | `Response wrapped in {success, data}` | 200 | PASS | |

## Bugs Found

None. All 25 tests passed. Hermit Agent changes had zero impact on the Merchant module.

## DashboardStats Field Reference

Actual field names returned by `GET /merchant/stats`:

| Field | Type | Description |
|-------|------|-------------|
| `today_revenue` | float | Revenue for current calendar day (UTC) |
| `today_orders` | int | Order count for current calendar day |
| `pending_orders` | int | All-time pending orders count |
| `low_stock_variants` | int | Variants at or below low_stock_alert threshold |
| `new_customers_today` | int | Customers created today |
| `revenue_change_pct` | float | % change vs yesterday |
| `orders_change_pct` | float | % change vs yesterday |

## Summary

- Tests executed: **25**
- Passed: **25** (all)
- Bugs found: **0**
- Hermit Agent changes: **no regressions**
