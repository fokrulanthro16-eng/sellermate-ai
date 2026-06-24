"""Auth regression QA — 8 endpoints, mirrors original AUTH_QA_REPORT."""
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
AUTH = "/api/v1/auth"


# ── helpers ───────────────────────────────────────────────────────────────────

def req(method, path, body=None, token=None, expected=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            status = resp.status
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            payload = json.loads(e.read())
        except Exception:
            payload = {}
    passed = (expected is None) or (status == expected)
    return status, payload, passed


results = []

def record(name, status, passed, payload=None):
    results.append((name, status, passed))
    icon = "PASS" if passed else "FAIL"
    snippet = json.dumps(payload)[:100] if payload else ""
    print(f"  [{icon}] {name} | HTTP {status}")
    if snippet:
        print(f"         {snippet}")

def sep(t):
    print(f"\n{'=' * 60}\n  {t}\n{'=' * 60}")


# ── unique credentials ─────────────────────────────────────────────────────────
ts   = str(int(time.time()))[-9:]
EMAIL = f"reg_auth_{ts}@example.com"
PHONE = f"+8801{ts}"
PASS  = "Regression123!"

sep("SETUP")
print(f"  Email: {EMAIL}\n  Phone: {PHONE}")


# ── T01: Register ─────────────────────────────────────────────────────────────
sep("T01  POST /auth/register")
status, payload, passed = req("POST", f"{AUTH}/register", {
    "email": EMAIL,
    "phone": PHONE,
    "password": PASS,
    "business_name": "Auth Regression Shop",
    "owner_name": "Regression Tester",
    "business_type": "ELECTRONICS",
}, expected=201)
record("T01 POST /register -> 201", status, passed, payload)

# Shape checks
merchant_data = payload.get("data", {}).get("merchant", {})
tokens_data   = payload.get("data", {}).get("tokens", {})
has_fields = all(k in merchant_data for k in ["id", "email", "phone", "business_name"])
has_tokens = all(k in tokens_data for k in ["access_token", "refresh_token", "token_type"])
record("T01 Response has merchant + tokens", status, has_fields and has_tokens)

access_token  = tokens_data.get("access_token", "")
refresh_token = tokens_data.get("refresh_token", "")

# Duplicate registration -> 409
status2, payload2, passed2 = req("POST", f"{AUTH}/register", {
    "email": EMAIL,
    "phone": PHONE,
    "password": PASS,
    "business_name": "Dupe",
    "owner_name": "Dupe Owner",
    "business_type": "OTHER",
}, expected=409)
record("T01 Duplicate register -> 409", status2, passed2, payload2)


# ── T02: Login ────────────────────────────────────────────────────────────────
sep("T02  POST /auth/login")
# Login with phone
status, payload, passed = req("POST", f"{AUTH}/login", {
    "identifier": PHONE,
    "password": PASS,
}, expected=200)
record("T02 POST /login (phone) -> 200", status, passed, payload)
login_tokens = payload.get("data", {}).get("tokens", {})
access_token  = login_tokens.get("access_token", access_token)
refresh_token = login_tokens.get("refresh_token", refresh_token)

# Login with email — this rotates the refresh token, so capture the new one
status, payload, passed = req("POST", f"{AUTH}/login", {
    "identifier": EMAIL,
    "password": PASS,
}, expected=200)
record("T02 POST /login (email) -> 200", status, passed)
email_tokens  = payload.get("data", {}).get("tokens", {})
access_token  = email_tokens.get("access_token", access_token)
refresh_token = email_tokens.get("refresh_token", refresh_token)

# Wrong password -> 401
status, payload, passed = req("POST", f"{AUTH}/login", {
    "identifier": PHONE,
    "password": "WrongPass999!",
}, expected=401)
record("T02 POST /login (bad password) -> 401", status, passed, payload)


# ── T03: Refresh ──────────────────────────────────────────────────────────────
sep("T03  POST /auth/refresh")
status, payload, passed = req("POST", f"{AUTH}/refresh", {
    "refresh_token": refresh_token,
}, expected=200)
record("T03 POST /refresh -> 200", status, passed, payload)
new_tokens = payload.get("data", {})
new_access  = new_tokens.get("access_token", "")
new_refresh = new_tokens.get("refresh_token", "")
has_both = bool(new_access and new_refresh)
record("T03 Refresh returns new token pair", status, has_both)
if new_access:
    access_token  = new_access
    refresh_token = new_refresh

# Invalid refresh token -> 401
status, payload, passed = req("POST", f"{AUTH}/refresh", {
    "refresh_token": "not.a.token",
}, expected=401)
record("T03 POST /refresh (bad token) -> 401", status, passed, payload)


# ── T04: /me ─────────────────────────────────────────────────────────────────
sep("T04  GET /auth/me")
status, payload, passed = req("GET", f"{AUTH}/me", token=access_token, expected=200)
record("T04 GET /me -> 200", status, passed, payload)
me_data = payload.get("data", {})
correct_identity = me_data.get("phone") == PHONE and me_data.get("email") == EMAIL
record("T04 /me returns correct merchant", status, correct_identity)

# No token -> 401
status, payload, passed = req("GET", f"{AUTH}/me", expected=401)
record("T04 GET /me (no token) -> 401", status, passed, payload)


# ── T05: Logout ───────────────────────────────────────────────────────────────
sep("T05  POST /auth/logout")
# Keep a separate token for logout test so we don't strand ourselves
status2, payload2, _ = req("POST", f"{AUTH}/login", {
    "identifier": PHONE, "password": PASS,
})
logout_token   = payload2.get("data", {}).get("tokens", {}).get("access_token", "")
logout_refresh = payload2.get("data", {}).get("tokens", {}).get("refresh_token", "")

status, payload, passed = req(
    "POST", f"{AUTH}/logout",
    body={"refresh_token": logout_refresh},
    token=logout_token,
    expected=200,
)
record("T05 POST /logout -> 200", status, passed, payload)

# After logout the access token must be blacklisted -> 401
status, payload, passed = req("GET", f"{AUTH}/me", token=logout_token, expected=401)
record("T05 Blacklisted token rejected after logout -> 401", status, passed, payload)


# ── T06: Forgot-password ──────────────────────────────────────────────────────
sep("T06  POST /auth/forgot-password")
status, payload, passed = req("POST", f"{AUTH}/forgot-password", {
    "phone": PHONE,
}, expected=200)
record("T06 POST /forgot-password -> 200", status, passed, payload)
otp = payload.get("data", {}).get("otp", "")
has_otp = bool(otp)
record("T06 OTP returned in dev mode", status, has_otp)
print(f"         OTP: {otp}")

# Valid-format but non-existent phone -> 404
status, payload, passed = req("POST", f"{AUTH}/forgot-password", {
    "phone": "+8801399999998",
}, expected=404)
record("T06 POST /forgot-password (unknown phone) -> 404", status, passed, payload)


# ── T07: Verify-OTP ───────────────────────────────────────────────────────────
sep("T07  POST /auth/verify-otp")
status, payload, passed = req("POST", f"{AUTH}/verify-otp", {
    "phone": PHONE,
    "otp": otp,
}, expected=200)
record("T07 POST /verify-otp (correct OTP) -> 200", status, passed, payload)

# Wrong OTP -> 400 (OTP not consumed by verify, so it still exists)
status, payload, passed = req("POST", f"{AUTH}/verify-otp", {
    "phone": PHONE,
    "otp": "000000",
}, expected=400)
record("T07 POST /verify-otp (wrong OTP) -> 400", status, passed, payload)


# ── T08: Reset-password ───────────────────────────────────────────────────────
sep("T08  POST /auth/reset-password")
NEW_PASS = "NewRegression456!"
status, payload, passed = req("POST", f"{AUTH}/reset-password", {
    "phone": PHONE,
    "otp": otp,
    "new_password": NEW_PASS,
}, expected=200)
record("T08 POST /reset-password -> 200", status, passed, payload)

# OTP must be consumed — second reset with same OTP -> 400
status, payload, passed = req("POST", f"{AUTH}/reset-password", {
    "phone": PHONE,
    "otp": otp,
    "new_password": "ThirdPass789!",
}, expected=400)
record("T08 POST /reset-password (OTP reuse) -> 400", status, passed, payload)

# Login with new password confirms the change
status, payload, passed = req("POST", f"{AUTH}/login", {
    "identifier": PHONE,
    "password": NEW_PASS,
}, expected=200)
record("T08 Login with new password -> 200", status, passed, payload)

# Old password rejected (401) or rate limited (429) — both mean login failed
status, payload, _ = req("POST", f"{AUTH}/login", {
    "identifier": PHONE,
    "password": PASS,
})
passed = status in (401, 429)
record("T08 Login with old password fails (401 or 429)", status, passed, payload)


# ── Summary ───────────────────────────────────────────────────────────────────
sep("RESULTS")
total  = len(results)
passed_n = sum(1 for _, _, p in results if p)
failed_n = total - passed_n

for name, sc, p in results:
    print(f"  [{'PASS' if p else 'FAIL'}] {name}")

print(f"\n  Total: {total}  |  Passed: {passed_n}  |  Failed: {failed_n}")
if failed_n == 0:
    print("\n  AUTH REGRESSION: ALL PASS")
else:
    print(f"\n  AUTH REGRESSION: {failed_n} FAILURE(S)")
    sys.exit(1)
