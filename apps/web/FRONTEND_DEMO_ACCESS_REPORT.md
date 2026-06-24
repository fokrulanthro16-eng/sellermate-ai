# Frontend Demo Access Mode — Implementation Report

## Overview

Demo Direct Access Mode lets anyone enter the SellerMate AI dashboard without manually filling in the registration form. A single button click provisions (or re-uses) a persistent demo account and lands the user on `/dashboard`.

---

## Files Changed / Created

| File | Change |
|------|--------|
| `src/lib/demo-auth.ts` | **New** — core demo logic (try-login → auto-register → retry-login) |
| `src/app/(auth)/login/page.tsx` | Added demo button + `handleDemoAccess` handler |
| `src/app/(auth)/register/page.tsx` | Added demo button + `handleDemoAccess` handler |

---

## Demo Credentials

| Field | Value |
|-------|-------|
| Email | `demo@sellermate.ai` |
| Phone | `+8801700000009` |
| Password | `Demo@123456` |
| Business name | `Demo Shop` |
| Owner name | `Demo Owner` |
| Business type | `FASHION_CLOTHING` |

---

## `enterDemoMode()` Logic

```
1. POST /auth/login  { identifier: "demo@sellermate.ai", password: "Demo@123456" }
   ✓ success  →  setTokens()  →  redirect /dashboard
   ✗ failure  →  account doesn't exist yet, continue ↓

2. POST /auth/register  { demo payload }
   ✓ success  →  account created, continue ↓
   ✗ failure  →  may already exist with same credentials; swallow error, continue ↓

3. POST /auth/login  (second attempt)
   ✓ success  →  setTokens()  →  redirect /dashboard
   ✗ failure  →  throw → toast.error in UI
```

This three-step approach is idempotent: clicking "ডেমো হিসেবে ঢুকুন" multiple times always works, whether the account exists or not. No backend change required.

---

## UI Changes

Both `/login` and `/register` now show:

```
[ লগইন করুন / অ্যাকাউন্ট তৈরি করুন ]

────── অথবা ──────

🧪  ডেমো হিসেবে ঢুকুন          ← amber-tinted outline button
```

- Normal login / register flows are unaffected.
- Both buttons are disabled while the other is in-flight (prevents double-submit).
- Loading spinner replaces icon during async call.
- Success → `toast.success("ডেমো মোডে স্বাগতম!")`.
- Failure → `toast.error(...)` with the API error message.

---

## Test Checklist

### /login demo button
- [ ] Navigate to `http://localhost:3000/login`
- [ ] Click **ডেমো হিসেবে ঢুকুন**
- [ ] Spinner appears on button, other button is disabled
- [ ] Toast: "ডেমো মোডে স্বাগতম!"
- [ ] Redirected to `/dashboard`
- [ ] `localStorage` contains `sellermate_token` and `sellermate_refresh`

### /register demo button
- [ ] Navigate to `http://localhost:3000/register`
- [ ] Click **ডেমো হিসেবে ঢুকুন**
- [ ] Same spinner / toast / redirect behaviour as above

### Dashboard loads after demo access
- [ ] Dashboard stat cards render (may show zeros if no data seeded)
- [ ] Sidebar nav is accessible
- [ ] Header shows merchant name "Demo Shop"
- [ ] Logout works (clears tokens, redirects to `/login`)

### Idempotency
- [ ] Click demo button, reach dashboard, logout
- [ ] Click demo button again — no registration error, same dashboard reached
- [ ] Repeat 3× — always succeeds

### Normal flows unbroken
- [ ] `/login` with real credentials still works
- [ ] `/register` with new credentials still works
- [ ] Demo button is disabled while normal form is submitting

---

## Notes

- The demo account is shared across all demo sessions. Any data created (products, orders, etc.) persists until the backend database is reset.
- `demo-auth.ts` path is `src/lib/demo-auth.ts` (inside `src/`, matching the project's path alias `@/lib/`). The requirement listed `apps/web/lib/demo-auth.ts` without `src/`; the file was placed at the correct resolved location.
- No backend endpoints, models, or configuration were modified.
