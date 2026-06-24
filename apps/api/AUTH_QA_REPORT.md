# AUTH QA REPORT

**Run:** 2026-06-21 (regression after Hermit Agent)  |  **Result:** 23/23 PASS

## Endpoint Results

| # | Test | HTTP | Status |
|---|------|------|--------|
| 1 | `POST /auth/register -> 201` | 201 | PASS |
| 2 | `POST /auth/register (duplicate) -> 409` | 409 | PASS |
| 3 | `Register response has merchant + tokens` | 201 | PASS |
| 4 | `POST /auth/login (phone) -> 200` | 200 | PASS |
| 5 | `POST /auth/login (email) -> 200` | 200 | PASS |
| 6 | `POST /auth/login (bad password) -> 401` | 401 | PASS |
| 7 | `POST /auth/refresh -> 200` | 200 | PASS |
| 8 | `Refresh returns new token pair` | 200 | PASS |
| 9 | `POST /auth/refresh (bad token) -> 401` | 401 | PASS |
| 10 | `GET /auth/me -> 200` | 200 | PASS |
| 11 | `/me returns correct merchant identity` | 200 | PASS |
| 12 | `GET /auth/me (no token) -> 401` | 401 | PASS |
| 13 | `POST /auth/logout -> 200` | 200 | PASS |
| 14 | `Blacklisted token rejected after logout -> 401` | 401 | PASS |
| 15 | `POST /auth/forgot-password -> 200` | 200 | PASS |
| 16 | `OTP returned in dev mode` | 200 | PASS |
| 17 | `POST /auth/forgot-password (unknown phone) -> 404` | 404 | PASS |
| 18 | `POST /auth/verify-otp (correct OTP) -> 200` | 200 | PASS |
| 19 | `POST /auth/verify-otp (wrong OTP) -> 400` | 400 | PASS |
| 20 | `POST /auth/reset-password -> 200` | 200 | PASS |
| 21 | `POST /auth/reset-password (OTP reuse) -> 400` | 400 | PASS |
| 22 | `Login with new password -> 200` | 200 | PASS |
| 23 | `Login with old password -> 401` | 401 | PASS |

## Bug Found & Fixed (this run)

### Bug: `POST /forgot-password` issued OTP for unknown phones

- **Symptom:** `POST /auth/forgot-password` with a non-existent phone number returned HTTP 200 and a valid OTP.
- **Root cause:** `send_otp()` in `auth_service.py` wrote to Redis without first verifying the phone exists in the DB. The router also didn't inject `db`.
- **Fix — `app/services/auth_service.py`:**
  - Added `NotFoundException` import.
  - `send_otp(redis, phone)` → `send_otp(db, redis, phone)` with a DB lookup before OTP generation; raises `NotFoundException` if not found.
- **Fix — `app/routers/auth.py`:**
  - `forgot_password(body, redis)` → `forgot_password(body, db, redis)` — injected `DB` dependency.
- **Impact:** No existing tests broken. The fix adds correct 404 behavior; known phones still receive OTPs as before.

## Summary

- Tests executed: **23**
- Passed: **23** (all)
- Bugs found & fixed: **1** (`forgot-password` phone existence check)
- Hermit Agent changes: **no regressions**
