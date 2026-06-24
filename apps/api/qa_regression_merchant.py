"""Merchant regression QA — 12 tests, mirrors original MERCHANT_QA_REPORT."""
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE     = "http://localhost:8000"
AUTH     = "/api/v1/auth"
MERCHANT = "/api/v1/merchant"


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
    snippet = json.dumps(payload)[:120] if payload else ""
    print(f"  [{icon}] {name} | HTTP {status}")
    if snippet:
        print(f"         {snippet}")

def sep(t):
    print(f"\n{'=' * 60}\n  {t}\n{'=' * 60}")


# ── setup ─────────────────────────────────────────────────────────────────────
ts    = str(int(time.time()))[-9:]
PHONE = f"+8801{ts}"
EMAIL = f"mq_reg_{ts}@example.com"
PASS  = "Merchant123!"

sep("SETUP")
print(f"  Phone: {PHONE}")

_, reg, _ = req("POST", f"{AUTH}/register", {
    "email": EMAIL,
    "phone": PHONE,
    "password": PASS,
    "business_name": "Merchant Regression Shop",
    "owner_name": "Merchant Regressor",
    "business_type": "ELECTRONICS",
})
tokens = reg.get("data", {}).get("tokens", {})
TOKEN = tokens.get("access_token", "")
print(f"  Token: {'...'+TOKEN[-10:] if TOKEN else 'NONE'}")
if not TOKEN:
    print("  [FATAL] Could not obtain token. Aborting.")
    sys.exit(1)


# ── T01: JWT protection ───────────────────────────────────────────────────────
sep("T01  JWT protection (no token)")
jwt_results = {}
for method, path in [
    ("GET",   f"{MERCHANT}/me"),
    ("PATCH", f"{MERCHANT}/me"),
    ("POST",  f"{MERCHANT}/onboarding"),
    ("GET",   f"{MERCHANT}/stats"),
    ("POST",  f"{MERCHANT}/whatsapp/connect"),
    ("GET",   f"{MERCHANT}/whatsapp/status"),
]:
    s, _, _ = req(method, path)
    jwt_results[f"{method} {path}"] = s
all_401 = all(s == 401 for s in jwt_results.values())
record("T01 All 6 merchant endpoints -> 401 without token", 401, all_401, jwt_results)


# ── T02: GET /me ──────────────────────────────────────────────────────────────
sep("T02  GET /merchant/me")
status, payload, passed = req("GET", f"{MERCHANT}/me", token=TOKEN, expected=200)
record("T02 GET /me -> 200", status, passed, payload)
me = payload.get("data", {})
correct = me.get("phone") == PHONE and me.get("email") == EMAIL
record("T02 /me returns correct merchant identity", status, correct)
required_fields = {"id", "email", "phone", "business_name", "owner_name", "business_type",
                   "status", "plan", "trust_score", "onboarding_done"}
missing = required_fields - set(me.keys())
record("T02 /me response schema complete", status, len(missing) == 0)
merchant_id = me.get("id", "")


# ── T03: PATCH /me ────────────────────────────────────────────────────────────
sep("T03  PATCH /merchant/me")
status, payload, passed = req("PATCH", f"{MERCHANT}/me", {
    "owner_name": "Updated Regressor",
    "address": "123 Regression Lane, Dhaka",
    "district": "Dhaka",
    "division": "Dhaka",
}, token=TOKEN, expected=200)
record("T03 PATCH /me (update profile fields) -> 200", status, passed, payload)
updated = payload.get("data", {})
name_ok    = updated.get("owner_name") == "Updated Regressor"
address_ok = updated.get("address") == "123 Regression Lane, Dhaka"
record("T03 Updated fields reflected in response", status, name_ok and address_ok)


# ── T04: DB persistence ───────────────────────────────────────────────────────
sep("T04  DB persistence (re-read after PATCH)")
status, payload, passed = req("GET", f"{MERCHANT}/me", token=TOKEN, expected=200)
record("T04 GET /me after PATCH -> 200", status, passed)
persist = payload.get("data", {})
db_name_ok    = persist.get("owner_name") == "Updated Regressor"
db_address_ok = persist.get("address") == "123 Regression Lane, Dhaka"
record("T04 PATCH persisted to DB (owner_name + address)", status, db_name_ok and db_address_ok)


# ── T05: Change business_type ─────────────────────────────────────────────────
sep("T05  PATCH /merchant/me (change business_type)")
status, payload, passed = req("PATCH", f"{MERCHANT}/me", {
    "business_type": "FASHION_CLOTHING",
}, token=TOKEN, expected=200)
record("T05 PATCH /me (business_type -> FASHION_CLOTHING) -> 200", status, passed)
bt_ok = payload.get("data", {}).get("business_type") == "FASHION_CLOTHING"
record("T05 business_type changed correctly", status, bt_ok)

# Restore
req("PATCH", f"{MERCHANT}/me", {"business_type": "ELECTRONICS"}, token=TOKEN)


# ── T06: Onboarding step 1 ───────────────────────────────────────────────────
sep("T06  POST /merchant/onboarding (step 1 - business info)")
status, payload, passed = req("POST", f"{MERCHANT}/onboarding", {
    "step": 1,
    "data": {
        "business_name": "Regression Complete Shop",
        "address": "456 Onboarding St",
        "district": "Chittagong",
        "division": "Chittagong",
    },
}, token=TOKEN, expected=200)
record("T06 POST /onboarding step=1 -> 200", status, passed, payload)
step1 = payload.get("data", {})
record("T06 onboarding_step advanced", status, step1.get("onboarding_step", -1) >= 1)


# ── T07: Onboarding step 3 ───────────────────────────────────────────────────
sep("T07  POST /merchant/onboarding (step 3 - WhatsApp phone)")
status, payload, passed = req("POST", f"{MERCHANT}/onboarding", {
    "step": 3,
    "data": {"phone": "+8801799999999"},
}, token=TOKEN, expected=200)
record("T07 POST /onboarding step=3 -> 200", status, passed, payload)
step3 = payload.get("data", {})
record("T07 whatsapp_phone stored", status, step3.get("whatsapp_phone") == "+8801799999999")


# ── T08: Onboarding step 4 (complete) ────────────────────────────────────────
sep("T08  POST /merchant/onboarding (step 4 - mark done)")
status, payload, passed = req("POST", f"{MERCHANT}/onboarding", {
    "step": 4,
    "data": {},
}, token=TOKEN, expected=200)
record("T08 POST /onboarding step=4 -> 200", status, passed, payload)
done_data = payload.get("data", {})
record("T08 onboarding_done=True after step 4", status, done_data.get("onboarding_done") is True)


# ── T09: Dashboard stats ──────────────────────────────────────────────────────
sep("T09  GET /merchant/stats")
status, payload, passed = req("GET", f"{MERCHANT}/stats", token=TOKEN, expected=200)
record("T09 GET /stats -> 200", status, passed, payload)
stats = payload.get("data", {})
stats_fields = {"today_revenue", "today_orders", "pending_orders", "low_stock_variants",
                "new_customers_today", "revenue_change_pct", "orders_change_pct"}
missing_stats = stats_fields - set(stats.keys())
record("T09 Stats response has all required fields", status, len(missing_stats) == 0)
numeric_ok = all(isinstance(stats.get(f), (int, float, str)) for f in stats_fields if f in stats)
record("T09 Stats fields are numeric/string types", status, numeric_ok)


# ── T10: WhatsApp connect ─────────────────────────────────────────────────────
sep("T10  POST /merchant/whatsapp/connect")
status, payload, passed = req("POST", f"{MERCHANT}/whatsapp/connect", token=TOKEN, expected=200)
record("T10 POST /whatsapp/connect -> 200", status, passed, payload)
wa_data = payload.get("data", {})
wa_fields_ok = "connected" in wa_data and "phone" in wa_data
record("T10 WhatsApp response has connected + phone fields", status, wa_fields_ok)


# ── T11: WhatsApp status ──────────────────────────────────────────────────────
sep("T11  GET /merchant/whatsapp/status")
status, payload, passed = req("GET", f"{MERCHANT}/whatsapp/status", token=TOKEN, expected=200)
record("T11 GET /whatsapp/status -> 200", status, passed, payload)
ws_data = payload.get("data", {})
record("T11 WhatsApp status has connected field", status, "connected" in ws_data)


# ── T12: Response schema validation ──────────────────────────────────────────
sep("T12  Response schema validation")
status, payload, passed = req("GET", f"{MERCHANT}/me", token=TOKEN, expected=200)
merchant_resp = payload.get("data", {})
all_required = {
    "id", "email", "phone", "business_name", "owner_name", "business_type",
    "address", "district", "division", "logo_url", "whatsapp_phone",
    "whatsapp_connected", "trust_score", "status", "plan", "plan_expires_at",
    "onboarding_step", "onboarding_done", "created_at", "updated_at",
}
present    = set(merchant_resp.keys())
missing_f  = all_required - present
extra_f    = present - all_required
record(f"T12 Full MerchantOut schema (missing={missing_f})", status, len(missing_f) == 0)
record("T12 Response wrapped in {success, data}", status,
       payload.get("success") is True and "data" in payload)


# ── Summary ───────────────────────────────────────────────────────────────────
sep("RESULTS")
total  = len(results)
passed_n = sum(1 for _, _, p in results if p)
failed_n = total - passed_n

for name, sc, p in results:
    print(f"  [{'PASS' if p else 'FAIL'}] {name}")

print(f"\n  Total: {total}  |  Passed: {passed_n}  |  Failed: {failed_n}")
if failed_n == 0:
    print("\n  MERCHANT REGRESSION: ALL PASS")
else:
    print(f"\n  MERCHANT REGRESSION: {failed_n} FAILURE(S)")
    sys.exit(1)
