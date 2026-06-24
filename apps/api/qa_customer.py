"""
Customer Module QA Script
Live-server functional QA for all 8 customer endpoints.
Start the API server before running: uvicorn app.main:app --reload
"""

import json
import time
import uuid
import http.client

BASE_HOST = "127.0.0.1"
BASE_PORT = 8000
CUST = "/api/v1/customers"
AUTH = "/api/v1/auth"

pass_count = 0
fail_count = 0

TOKEN_A = None
TOKEN_B = None
CUSTOMER_ID = None


def req(method, path, *, token=None, body=None, expected=200):
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=15)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    raw_body = json.dumps(body) if body else None
    conn.request(method, path, body=raw_body, headers=headers)
    resp = conn.getresponse()
    status = resp.status
    raw = resp.read()
    try:
        payload = json.loads(raw) if raw else {}
    except Exception:
        payload = {"_raw": raw.decode("utf-8", errors="replace")[:200]}
    conn.close()
    return status, payload, status == expected


def req_raw(method, path, *, token=None):
    """Return raw bytes (for CSV download)."""
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=15)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request(method, path, headers=headers)
    resp = conn.getresponse()
    status = resp.status
    raw = resp.read()
    ct = resp.getheader("Content-Type", "")
    conn.close()
    return status, raw, ct


def record(label, status, passed, payload=None):
    global pass_count, fail_count
    mark = "[PASS]" if passed else "[FAIL]"
    if passed:
        pass_count += 1
    else:
        fail_count += 1
    snippet = ""
    if payload and not passed:
        snippet = f"\n         {json.dumps(payload)[:120]}"
    print(f"  {mark} {label} | HTTP {status}{snippet}")


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ── Setup ────────────────────────────────────────────────────────
section("SETUP — register two merchants")

ts  = str(int(time.time()))[-9:]
ts2 = str(int(time.time()) + 1)[-9:]
PHONE_M_A = f"+8801{ts}"
PHONE_M_B = f"+8801{ts2}"
PASS = "SecurePass123!"

for label, phone, ts_val in [("Merchant A", PHONE_M_A, ts), ("Merchant B", PHONE_M_B, ts2)]:
    for attempt in range(3):
        status, data, _ = req("POST", f"{AUTH}/register", body={
            "email": f"cust_qa_{ts_val}@example.com",
            "phone": phone,
            "password": PASS,
            "business_name": f"Cust Biz {label}",
            "owner_name": label,
            "business_type": "FASHION_CLOTHING",
        }, expected=201)
        if status in (201, 409):
            break
        if status == 429:
            time.sleep(12)
    else:
        print(f"  [ERROR] {label} register failed: {status} {data}")

status, data, _ = req("POST", f"{AUTH}/login", body={"identifier": PHONE_M_A, "password": PASS})
TOKEN_A = data.get("data", {}).get("tokens", {}).get("access_token")

status, data, _ = req("POST", f"{AUTH}/login", body={"identifier": PHONE_M_B, "password": PASS})
TOKEN_B = data.get("data", {}).get("tokens", {}).get("access_token")

print(f"  Merchant A token={'OK' if TOKEN_A else 'FAIL'}")
print(f"  Merchant B token={'OK' if TOKEN_B else 'FAIL'}")

# ── T01: JWT protection ───────────────────────────────────────────
section("T01  JWT protection — all 8 endpoints require auth")

endpoints = [
    ("GET",    CUST),
    ("POST",   CUST),
    ("GET",    f"{CUST}/export"),
    ("GET",    f"{CUST}/00000000-0000-0000-0000-000000000000"),
    ("PATCH",  f"{CUST}/00000000-0000-0000-0000-000000000000"),
    ("DELETE", f"{CUST}/00000000-0000-0000-0000-000000000000"),
    ("POST",   f"{CUST}/00000000-0000-0000-0000-000000000000/tags/vip"),
    ("DELETE", f"{CUST}/00000000-0000-0000-0000-000000000000/tags/vip"),
]
all_401 = all(req(m, p, expected=401)[0] == 401 for m, p in endpoints)
record("T01 All 8 endpoints return 401 without token", 401 if all_401 else 0, all_401)

# ── T02: Create customer ──────────────────────────────────────────
section("T02  POST /customers — create customer")

c_phone = f"+88015{ts[-8:]}"
status, data, passed = req("POST", CUST, token=TOKEN_A, body={
    "name": "Alice Rahman",
    "phone": c_phone,
    "email": "alice@example.com",
    "district": "Dhaka",
    "division": "Dhaka",
    "notes": "VIP customer",
    "tags": ["vip", "regular"],
    "source": "MANUAL",
}, expected=201)
record("T02 POST /customers -> 201", status, passed, data)

CUSTOMER_ID = data.get("data", {}).get("id")
record("T02 Response has customer ID", status, bool(CUSTOMER_ID), data)

c = data.get("data", {})
record("T02 total_orders=0 by default", status, c.get("total_orders") == 0, c)
record("T02 total_spent=0 by default", status, str(c.get("total_spent")) in ("0", "0.00", "0E-2"), c)
record("T02 tags stored correctly", status, set(c.get("tags", [])) == {"vip", "regular"}, c)
record("T02 source=MANUAL", status, c.get("source") == "MANUAL", c)

# ── T03: Duplicate phone ──────────────────────────────────────────
section("T03  POST /customers — duplicate phone")

status, data, passed = req("POST", CUST, token=TOKEN_A, body={
    "name": "Alice Clone",
    "phone": c_phone,
}, expected=409)
record("T03 Duplicate phone -> 409", status, passed, data)

# ── T04: Invalid phone format ─────────────────────────────────────
section("T04  POST /customers — invalid phone")

status, data, passed = req("POST", CUST, token=TOKEN_A, body={
    "name": "Bob",
    "phone": "not-a-phone",
}, expected=422)
record("T04 Invalid phone -> 422", status, passed, data)

# ── T05: Get customer by ID ───────────────────────────────────────
section("T05  GET /customers/{id} — get by ID")

status, data, passed = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A, expected=200)
record("T05 GET /customers/{id} -> 200", status, passed, data)

c = data.get("data", {})
has_fields = all(k in c for k in ["id", "merchant_id", "name", "phone", "email",
                                   "total_orders", "total_spent", "tags", "source",
                                   "created_at", "updated_at"])
record("T05 CustomerOut has all required fields", status, has_fields, c)
record("T05 Phone correct", status, c.get("phone") == c_phone, c)

# ── T06: Get nonexistent customer ─────────────────────────────────
section("T06  GET /customers/{id} — not found")

status, data, passed = req("GET", f"{CUST}/{str(uuid.uuid4())}", token=TOKEN_A, expected=404)
record("T06 Unknown customer -> 404", status, passed, data)

# ── T07: Update customer ──────────────────────────────────────────
section("T07  PATCH /customers/{id} — update")

status, data, passed = req("PATCH", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A, body={
    "name": "Alice Rahman Updated",
    "district": "Chittagong",
    "notes": "Updated notes",
}, expected=200)
record("T07 PATCH /customers/{id} -> 200", status, passed, data)

c = data.get("data", {})
record("T07 name updated", status, c.get("name") == "Alice Rahman Updated", c)
record("T07 district updated", status, c.get("district") == "Chittagong", c)
record("T07 notes updated", status, c.get("notes") == "Updated notes", c)

# ── T08: List customers ───────────────────────────────────────────
section("T08  GET /customers — list with pagination")

# Create a second customer for list tests
c2_phone = f"+88016{ts[-8:]}"
req("POST", CUST, token=TOKEN_A, body={
    "name": "Bob Hossain",
    "phone": c2_phone,
    "district": "Chittagong",
    "tags": ["wholesale"],
}, expected=201)

status, data, passed = req("GET", CUST, token=TOKEN_A, expected=200)
record("T08 GET /customers -> 200", status, passed, data)

has_meta = "meta" in data
record("T08 Response has pagination meta", status, has_meta, data)
items = data.get("data", [])
record("T08 At least 2 customers returned", status, len(items) >= 2, data)

# ── T09: Search ───────────────────────────────────────────────────
section("T09  GET /customers — search by name")

status, data, passed = req("GET", f"{CUST}?search=Alice", token=TOKEN_A, expected=200)
record("T09 Search 'Alice' -> 200", status, passed, data)
results = data.get("data", [])
alice_found = any("alice" in c.get("name", "").lower() for c in results)
record("T09 Alice appears in search results", status, alice_found, results)

status2, data2, _ = req("GET", f"{CUST}?search=xyznotfound999", token=TOKEN_A, expected=200)
empty = len(data2.get("data", [])) == 0
record("T09 Search no match -> empty list", status2, empty, data2)

# ── T10: District filter ──────────────────────────────────────────
section("T10  GET /customers — district filter")

status, data, passed = req("GET", f"{CUST}?district=Chittagong", token=TOKEN_A, expected=200)
record("T10 District filter -> 200", status, passed, data)
district_results = data.get("data", [])
all_district = all(c.get("district") == "Chittagong" for c in district_results)
record("T10 All results are from Chittagong", status, all_district and len(district_results) > 0, district_results)

# ── T11: Tags filter ──────────────────────────────────────────────
section("T11  GET /customers — tags filter (Bug 1 fix)")

status, data, passed = req("GET", f"{CUST}?tags=vip", token=TOKEN_A, expected=200)
record("T11 Tags filter -> 200", status, passed, data)
tag_results = data.get("data", [])
all_have_vip = all("vip" in c.get("tags", []) for c in tag_results)
record("T11 All returned customers have 'vip' tag", status, all_have_vip and len(tag_results) > 0, tag_results)
wholesale_not_in_vip = not any("wholesale" in c.get("tags", []) and "vip" not in c.get("tags", []) for c in tag_results)
record("T11 wholesale-only customer excluded from vip filter", status, wholesale_not_in_vip, tag_results)

# ── T12: Pagination ───────────────────────────────────────────────
section("T12  GET /customers — pagination")

status, data, passed = req("GET", f"{CUST}?page=1&limit=1", token=TOKEN_A, expected=200)
record("T12 limit=1 -> 200", status, passed, data)
meta = data.get("meta", {})
record("T12 meta.limit=1", status, meta.get("limit") == 1, meta)
record("T12 total >= 2", status, meta.get("total", 0) >= 2, meta)
page_items = data.get("data", [])
record("T12 At most 1 result returned", status, len(page_items) <= 1, page_items)

# ── T13: Add tag ──────────────────────────────────────────────────
section("T13  POST /customers/{id}/tags/{tag} — add tag")

status, data, passed = req("POST", f"{CUST}/{CUSTOMER_ID}/tags/premium", token=TOKEN_A, expected=200)
record("T13 Add tag 'premium' -> 200", status, passed, data)
tags_now = data.get("data", {}).get("tags", [])
record("T13 'premium' tag added", status, "premium" in tags_now, tags_now)
record("T13 Previous tags preserved", status, "vip" in tags_now, tags_now)

# ── T14: Add duplicate tag (idempotent) ───────────────────────────
section("T14  POST /customers/{id}/tags/{tag} — duplicate tag ignored")

status, data, _ = req("POST", f"{CUST}/{CUSTOMER_ID}/tags/premium", token=TOKEN_A, expected=200)
tags_after = data.get("data", {}).get("tags", [])
count_premium = tags_after.count("premium")
record("T14 Duplicate tag not added twice", status, count_premium == 1, tags_after)

# ── T15: Remove tag ───────────────────────────────────────────────
section("T15  DELETE /customers/{id}/tags/{tag} — remove tag")

status, data, passed = req("DELETE", f"{CUST}/{CUSTOMER_ID}/tags/premium", token=TOKEN_A, expected=200)
record("T15 Remove tag 'premium' -> 200", status, passed, data)
tags_after_remove = data.get("data", {}).get("tags", [])
record("T15 'premium' tag removed", status, "premium" not in tags_after_remove, tags_after_remove)
record("T15 'vip' tag still present", status, "vip" in tags_after_remove, tags_after_remove)

# ── T16: Merchant isolation — list ───────────────────────────────
section("T16  Merchant isolation")

status, data, _ = req("GET", CUST, token=TOKEN_B, expected=200)
b_items = data.get("data", [])
a_ids = [c.get("id") for c in items]
b_sees_a = any(c.get("id") in a_ids for c in b_items)
record("T16 Merchant B's list excludes Merchant A's customers", status, not b_sees_a, b_items)

# Merchant B cannot GET Merchant A's customer
status, data, passed = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_B, expected=404)
record("T16 Merchant B cannot GET Merchant A's customer -> 404", status, passed, data)

# Merchant B cannot PATCH Merchant A's customer
status, data, passed = req("PATCH", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_B, body={"name": "Hacked"}, expected=404)
record("T16 Merchant B cannot PATCH Merchant A's customer -> 404", status, passed, data)

# Verify name unchanged
status, data, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A, expected=200)
record("T16 Merchant A's customer name unchanged after isolation attack", status,
       data.get("data", {}).get("name") == "Alice Rahman Updated", data)

# ── T17: CSV Export ───────────────────────────────────────────────
section("T17  GET /customers/export — CSV download")

status, raw, ct = req_raw("GET", f"{CUST}/export", token=TOKEN_A)
record("T17 GET /customers/export -> 200", status, status == 200)
record("T17 Content-Type is text/csv", status, "text/csv" in ct)
csv_text = raw.decode("utf-8-sig", errors="replace")
record("T17 CSV has header row", status, "name,phone" in csv_text.replace('"', ''))
record("T17 CSV contains Alice", status, "Alice" in csv_text)
record("T17 Export requires auth", 401, req_raw("GET", f"{CUST}/export")[0] == 401, None)

# ── T18: Delete customer ──────────────────────────────────────────
section("T18  DELETE /customers/{id} — delete")

# Create a fresh customer with no orders to delete
del_phone = f"+88017{ts2[-8:]}"
status, data, _ = req("POST", CUST, token=TOKEN_A, body={
    "name": "Temp Customer",
    "phone": del_phone,
}, expected=201)
DEL_ID = data.get("data", {}).get("id")

status, data, passed = req("DELETE", f"{CUST}/{DEL_ID}", token=TOKEN_A, expected=200)
record("T18 DELETE /customers/{id} -> 200", status, passed, data)
record("T18 Response has success message", status, "message" in data, data)

# Verify deleted
status2, _, _ = req("GET", f"{CUST}/{DEL_ID}", token=TOKEN_A, expected=404)
record("T18 Deleted customer no longer accessible -> 404", status2, status2 == 404)

# ── T19: Delete nonexistent ───────────────────────────────────────
section("T19  DELETE /customers/{id} — not found")

status, data, passed = req("DELETE", f"{CUST}/{str(uuid.uuid4())}", token=TOKEN_A, expected=404)
record("T19 Delete unknown customer -> 404", status, passed, data)

# ── T20: DB persistence ───────────────────────────────────────────
section("T20  DB persistence — customer survives separate requests")

status, data, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A, expected=200)
c = data.get("data", {})
record("T20 Customer persists after multiple requests", status,
       c.get("id") == CUSTOMER_ID and c.get("name") == "Alice Rahman Updated")

status2, data2, _ = req("PATCH", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A, body={"notes": "persistence test"})
status3, data3, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A)
record("T20 Update persists across requests", status3,
       data3.get("data", {}).get("notes") == "persistence test")

# ── Summary ──────────────────────────────────────────────────────
total = pass_count + fail_count
print(f"\n{'=' * 60}")
print(f"  QA RESULTS: {pass_count}/{total} PASS  |  {fail_count} FAIL")
print("=" * 60)
if fail_count:
    print("  STATUS: NEEDS REVIEW")
else:
    print("  STATUS: ALL PASS")
