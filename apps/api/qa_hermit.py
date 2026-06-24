"""Hermit Agent QA — end-to-end tests for all three endpoints."""
import sys
import time
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"


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
    icon = "PASS" if passed else "FAIL"
    return status, payload, passed, icon


def sep(title=""):
    print(f"\n{'=' * 60}")
    if title:
        print(f"  {title}")
        print(f"{'=' * 60}")


results = []

def record(name, status, payload, passed):
    results.append((name, status, passed))
    snippet = json.dumps(payload)[:120]
    icon = "PASS" if passed else "FAIL"
    print(f"[{icon}] {name} | HTTP {status}")
    print(f"       {snippet}")


# ── setup: register + login ───────────────────────────────────────────────────
sep("SETUP")
suffix = str(int(time.time()))[-9:]  # 9 digits -> +8801XXXXXXXXX

_, reg, _, _ = req("POST", "/api/v1/auth/register", {
    "email": f"hermit{suffix}@example.com",
    "phone": f"+8801{suffix}",
    "password": "HermitPass123!",
    "business_name": "Hermit Test Shop",
    "owner_name": "Hermit Tester",
    "business_type": "OTHER",
})
print(f"Register -> {reg.get('success')}")

_, login_r, _, _ = req("POST", "/api/v1/auth/login", {
    "identifier": f"+8801{suffix}",
    "password": "HermitPass123!",
})
token = login_r.get("data", {}).get("tokens", {}).get("access_token", "")
print(f"Login -> token={'...' + token[-10:] if token else 'NONE'}")


# ── T01: JWT protection ───────────────────────────────────────────────────────
sep("T01  JWT protection (no token)")
for path in [
    "/api/v1/ai/hermit/run",
    "/api/v1/ai/hermit/insights",
]:
    method = "POST" if "run" in path else "GET"
    status, payload, passed, icon = req(method, path, expected=401)
    record(f"T01 {method} {path} -> 401", status, payload, passed)


# ── T02: POST /run (no prior data) ───────────────────────────────────────────
sep("T02  POST /api/v1/ai/hermit/run (fresh merchant, no orders)")
status, payload, passed, icon = req("POST", "/api/v1/ai/hermit/run", token=token, expected=200)
record("T02 POST /run", status, payload, passed)
run_data = payload.get("data", {})
print(f"       insights_generated={run_data.get('insights_generated')}  cleared={run_data.get('cleared')}")
print(f"       breakdown={run_data.get('breakdown')}")
assert run_data.get("insights_generated") is not None, "missing insights_generated"


# ── T03: GET /insights ────────────────────────────────────────────────────────
sep("T03  GET /api/v1/ai/hermit/insights")
status, payload, passed, icon = req("GET", "/api/v1/ai/hermit/insights", token=token, expected=200)
record("T03 GET /insights", status, payload, passed)
insights_list = payload.get("data", [])
print(f"       returned {len(insights_list)} insight(s)")

# There should always be at least the weekly health insight
weekly = [i for i in insights_list if i.get("insight_type") == "WEEKLY_HEALTH"]
weekly_ok = len(weekly) == 1
print(f"       WEEKLY_HEALTH present: {weekly_ok}")
if not weekly_ok:
    print("       [FAIL] Expected exactly 1 WEEKLY_HEALTH insight")
    results.append(("T03-WEEKLY_HEALTH", 200, False))
else:
    results.append(("T03-WEEKLY_HEALTH", 200, True))

# Validate shape of first insight
if insights_list:
    required_fields = {"id", "merchant_id", "insight_type", "severity", "title", "body", "meta", "is_read", "generated_at"}
    first = insights_list[0]
    missing = required_fields - set(first.keys())
    schema_ok = len(missing) == 0
    print(f"       Schema check -> {'PASS' if schema_ok else 'FAIL missing=' + str(missing)}")
    results.append(("T03-SCHEMA", 200, schema_ok))


# ── T04: filter by insight_type ───────────────────────────────────────────────
sep("T04  GET /insights?insight_type=WEEKLY_HEALTH")
status, payload, passed, icon = req(
    "GET", "/api/v1/ai/hermit/insights?insight_type=WEEKLY_HEALTH", token=token, expected=200
)
record("T04 GET /insights?insight_type=WEEKLY_HEALTH", status, payload, passed)
filtered = payload.get("data", [])
filter_ok = all(i["insight_type"] == "WEEKLY_HEALTH" for i in filtered) and len(filtered) >= 1
print(f"       filter_ok={filter_ok}  count={len(filtered)}")
results.append(("T04-FILTER-TYPE", 200, filter_ok))


# ── T05: filter by severity ────────────────────────────────────────────────────
sep("T05  GET /insights?severity=INFO")
status, payload, passed, icon = req(
    "GET", "/api/v1/ai/hermit/insights?severity=INFO", token=token, expected=200
)
record("T05 GET /insights?severity=INFO", status, payload, passed)
info_insights = payload.get("data", [])
sev_ok = all(i["severity"] == "INFO" for i in info_insights)
print(f"       severity_filter_ok={sev_ok}  count={len(info_insights)}")
results.append(("T05-FILTER-SEVERITY", 200, sev_ok))


# ── T06: filter unread_only ────────────────────────────────────────────────────
sep("T06  GET /insights?unread_only=true")
status, payload, passed, icon = req(
    "GET", "/api/v1/ai/hermit/insights?unread_only=true", token=token, expected=200
)
record("T06 GET /insights?unread_only=true", status, payload, passed)
unread = payload.get("data", [])
unread_ok = all(not i["is_read"] for i in unread)
print(f"       all_unread={unread_ok}  count={len(unread)}")
results.append(("T06-FILTER-UNREAD", 200, unread_ok))


# ── T07: PATCH /insights/{id}/read ────────────────────────────────────────────
sep("T07  PATCH /insights/{id}/read")
if insights_list:
    insight_id = insights_list[0]["id"]
    status, payload, passed, icon = req(
        "PATCH", f"/api/v1/ai/hermit/insights/{insight_id}/read", token=token, expected=200
    )
    record(f"T07 PATCH /insights/{insight_id[:8]}../read", status, payload, passed)
    marked = payload.get("data", {}).get("marked_read")
    print(f"       marked_read={marked}")
    results.append(("T07-MARK-READ", status, passed and marked is True))

    # Verify it's now excluded from unread_only
    _, after, _, _ = req(
        "GET", f"/api/v1/ai/hermit/insights?unread_only=true", token=token
    )
    after_ids = [i["id"] for i in after.get("data", [])]
    not_in_unread = insight_id not in after_ids
    print(f"       removed_from_unread_list={not_in_unread}")
    results.append(("T07-READ-HIDDEN-FROM-UNREAD", 200, not_in_unread))

    # PATCH a fake ID -> 404
    status, payload, passed, icon = req(
        "PATCH", "/api/v1/ai/hermit/insights/nonexistent-id/read", token=token, expected=404
    )
    record("T07 PATCH /insights/nonexistent/read -> 404", status, payload, passed)
else:
    print("  [SKIP] No insights available to mark read")


# ── T08: idempotent re-run clears previous insights ───────────────────────────
sep("T08  POST /run again — idempotency (clears + regenerates)")
status, payload, passed, icon = req("POST", "/api/v1/ai/hermit/run", token=token, expected=200)
record("T08 POST /run (2nd call)", status, payload, passed)
run2 = payload.get("data", {})
print(f"       insights_generated={run2.get('insights_generated')}  cleared={run2.get('insights_cleared')}")
idempotent_ok = run2.get("insights_cleared", 0) > 0
print(f"       previous_cleared={idempotent_ok}")
results.append(("T08-IDEMPOTENT", 200, idempotent_ok and passed))


# ── T09: merchant isolation ────────────────────────────────────────────────────
sep("T09  Merchant isolation (Merchant B cannot read Merchant A's insights)")
suffix2 = str(int(time.time()) + 1)[-9:]  # offset by 1 to avoid collision
req("POST", "/api/v1/auth/auth/register", {
    "email": f"hermitb{suffix2}@example.com",
    "phone": f"+8801{suffix2}",
    "password": "PassB123!",
    "business_name": "Hermit Shop B",
    "owner_name": "Owner B Two",
    "business_type": "OTHER",
})
_, login_b, _, _ = req("POST", "/api/v1/auth/auth/login", {
    "identifier": f"+8801{suffix2}",
    "password": "PassB123!",
})
token_b = login_b.get("data", {}).get("tokens", {}).get("access_token", "")

# B runs its own analysis (gets its own insights)
req("POST", "/api/v1/ai/hermit/run", token=token_b)
_, b_insights, _, _ = req("GET", "/api/v1/ai/hermit/insights", token=token_b)

# Check that none of B's insights have merchant_id belonging to A
_, a_me, _, _ = req("GET", "/api/v1/auth/auth/me", token=token)
a_merchant_id = a_me.get("data", {}).get("id", "")
b_data = b_insights.get("data", [])
isolation_ok = all(i.get("merchant_id") != a_merchant_id for i in b_data) if b_data else True
print(f"       A merchant_id={a_merchant_id[:8]}...")
print(f"       B insights not leaking A's data: {isolation_ok}")
record("T09 Isolation: B cannot see A's insights", 200, {"ok": isolation_ok}, isolation_ok)


# ── Summary ───────────────────────────────────────────────────────────────────
sep("RESULTS")
total = len(results)
passed_count = sum(1 for _, _, p in results if p)
failed_count = total - passed_count

print(f"\n  {'Test':<45} {'Status'}")
print(f"  {'-'*45} {'------'}")
for name, status_code, p in results:
    icon = "PASS" if p else "FAIL"
    print(f"  [{icon}] {name:<45}")

print(f"\n  Total: {total}  |  Passed: {passed_count}  |  Failed: {failed_count}")
if failed_count == 0:
    print("\n  ALL HERMIT QA TESTS PASSED")
else:
    print(f"\n  {failed_count} TEST(S) FAILED")
    sys.exit(1)
