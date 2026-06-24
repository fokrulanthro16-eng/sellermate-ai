# Frontend Runtime Fix Report

## Problem

Runtime crash across all paginated list pages:

```
TypeError: Cannot read properties of undefined (reading 'length')
```

or

```
TypeError: Cannot read properties of undefined (reading 'map')
```

## Root Cause

The TanStack Query hooks return paginated responses shaped as `{ items: T[], total: number }`. When the backend returns an error, a 404, or a response with `items: null`, the pattern `data?.items.length` does not protect against the crash.

**Why `data?.items.length` is unsafe:**
- `data?.items` uses optional chaining on `data`, so if `data` is `undefined`, it returns `undefined`.
- But `data?.items.length` is parsed as `(data?.items).length` — if `data` is defined but `data.items` is `null` or `undefined`, the `.length` access still throws.
- Same issue applies to `.map(...)`.

**Why pagination math is unsafe:**
- `Math.ceil(data.total / 20)` produces `NaN` when `data.total` is `null` or `undefined`.
- `data && data.total > 20` allows `data.total = null` to pass the truthiness check, then `null > 20` evaluates `false` but `Math.ceil(null / 20)` = `0` which is not 1.

## Fix Pattern Applied

For every paginated list page:

```tsx
// Before (unsafe)
data?.items.length === 0          // crashes if data.items is null
data?.items.map((x) => ...)       // crashes if data.items is null
Math.ceil(data.total / LIMIT)     // NaN if data.total is null
data && data.total > LIMIT        // unsafe if data.total is null

// After (safe)
const items = Array.isArray(data?.items) ? data.items : [];
const total = data?.total ?? 0;
const totalPages = Math.max(1, Math.ceil(total / LIMIT));

items.length === 0                // always works — items is always an array
items.map((x) => ...)             // always works
total > LIMIT                     // 0 > 20 = false — safe
totalPages                        // always >= 1 — safe
```

## Files Fixed

| File | Variables | Issues Resolved |
|------|-----------|----------------|
| `src/app/(dashboard)/orders/page.tsx` | `orders`, `total`, `totalPages` | `.length`, `.map`, pagination NaN |
| `src/app/(dashboard)/products/page.tsx` | `products`, `total`, `totalPages` | `.map` in grid view, pagination NaN |
| `src/app/(dashboard)/customers/page.tsx` | `customers`, `total`, `totalPages` | `.length`, `.map`, pagination NaN |
| `src/app/(dashboard)/inventory/page.tsx` | `inventoryItems`, `alerts`, `total`, `totalPages` | InventoryTable null prop, alerts undefined, pagination NaN |

## Files Audited (No Changes Needed)

| File | Status |
|------|--------|
| `src/app/(dashboard)/analytics/page.tsx` | Safe — uses `revenue \|\| []`, `topProducts \|\| []`, `?.` throughout |
| `src/app/(dashboard)/dashboard/page.tsx` | Safe — already fixed in previous session (safeNum pattern) |

## TypeScript Verification

```
npx tsc --noEmit
```

Exit code: **0** — no type errors.
