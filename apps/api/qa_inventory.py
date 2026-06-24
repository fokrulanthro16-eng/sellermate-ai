"""
Inventory Module QA Script
Live-server functional QA for all 4 inventory endpoints.
Start the API server before running: uvicorn app.main:app --reload
"""

import json
import time
import uuid
import http.client

BASE_HOST = "127.0.0.1"
BASE_PORT = 8000
INV = "/api/v1/inventory"
AUTH = "/api/v1/auth"
PROD = "/api/v1/products"

pass_count = 0
fail_count = 0

PHONE_A = f"+880170{int(time.time()) % 10000000:07d}"
PHONE_B = f"+880170{(int(time.time()) + 1) % 10000000:07d}"
TOKEN_A = None
TOKEN_B = None
MERCHANT_A_ID = None


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
    payload = json.loads(raw) if raw else {}
    conn.close()
    return status, payload, status == expected


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
section("SETUP — register two merchants + product with variants")

ts  = str(int(time.time()))[-9:]
ts2 = str(int(time.time()) + 1)[-9:]
PHONE_A = f"+8801{ts}"
PHONE_B = f"+8801{ts2}"
PASS = "SecurePass123!"

for label, phone, ts_val in [("Merchant A", PHONE_A, ts), ("Merchant B", PHONE_B, ts2)]:
    for attempt in range(3):
        status, data, _ = req("POST", f"{AUTH}/register", body={
            "email": f"inv_qa_{ts_val}@example.com",
            "phone": phone,
            "password": PASS,
            "business_name": f"Inv Biz {label}",
            "owner_name": label,
            "business_type": "FASHION_CLOTHING",
        }, expected=201)
        if status in (201, 409):
            break
        if status == 429:
            time.sleep(12)  # wait for rate-limit window to reset
    else:
        print(f"  [ERROR] {label} register failed: {status} {data}")

status, data, _ = req("POST", f"{AUTH}/login", body={
    "identifier": PHONE_A, "password": PASS,
}, expected=200)
TOKEN_A = data.get("data", {}).get("tokens", {}).get("access_token")
MERCHANT_A_ID = data.get("data", {}).get("merchant", {}).get("id")

status, data, _ = req("POST", f"{AUTH}/login", body={
    "identifier": PHONE_B, "password": PASS,
}, expected=200)
TOKEN_B = data.get("data", {}).get("tokens", {}).get("access_token")

print(f"  Merchant A token={'OK' if TOKEN_A else 'FAIL'}")
print(f"  Merchant B token={'OK' if TOKEN_B else 'FAIL'}")

# Create a product with 2 variants for Merchant A
sku_prefix = ts
status, data, _ = req("POST", PROD, token=TOKEN_A, body={
    "name": "QA Inventory Product",
    "category": "CLOTHING",
    "base_price": 150,
    "variants": [
        {"name": "Red M", "sku": f"INV-RED-{sku_prefix}", "stock_quantity": 50, "low_stock_alert": 10},
        {"name": "Blue L", "sku": f"INV-BLU-{sku_prefix}", "stock_quantity": 20, "low_stock_alert": 5},
    ],
}, expected=201)

PRODUCT_ID = data.get("data", {}).get("id")
# GET product detail to retrieve variant IDs (create returns ProductOut without variants)
_, detail, _ = req("GET", f"{PROD}/{PRODUCT_ID}", token=TOKEN_A, expected=200)
VARIANTS = detail.get("data", {}).get("variants", [])
VARIANT_A_ID = VARIANTS[0]["id"] if len(VARIANTS) > 0 else None
VARIANT_B_ID = VARIANTS[1]["id"] if len(VARIANTS) > 1 else None
print(f"  Product: {PRODUCT_ID}")
print(f"  Variant A (Red M, stock=50): {VARIANT_A_ID}")
print(f"  Variant B (Blue L, stock=20): {VARIANT_B_ID}")

# Create Merchant B's product/variant for isolation tests
status, data, _ = req("POST", PROD, token=TOKEN_B, body={
    "name": "Merchant B Product",
    "category": "CLOTHING",
    "base_price": 120,
    "variants": [{"name": "Default", "sku": f"MB-{sku_prefix}", "stock_quantity": 30}],
}, expected=201)
mb_pid = data.get("data", {}).get("id")
_, mb_detail, _ = req("GET", f"{PROD}/{mb_pid}", token=TOKEN_B, expected=200)
MB_VARIANT_ID = (mb_detail.get("data", {}).get("variants") or [{}])[0].get("id")
print(f"  Merchant B variant: {MB_VARIANT_ID}")

# ── T01: JWT protection ───────────────────────────────────────────
section("T01  JWT protection — all 4 endpoints require auth")

endpoints = [
    ("GET", INV),
    ("POST", f"{INV}/adjust"),
    ("GET", f"{INV}/alerts"),
    ("GET", f"{INV}/logs"),
]
all_401 = True
for method, path in endpoints:
    s, _, ok = req(method, path, expected=401)
    if s != 401:
        all_401 = False
record("T01 All 4 inventory endpoints return 401 without token", 401 if all_401 else 0, all_401)

# ── T02: List stock ───────────────────────────────────────────────
section("T02  GET /inventory — list all stock")

status, data, passed = req("GET", INV, token=TOKEN_A, expected=200)
record("T02 GET /inventory -> 200", status, passed, data)

has_meta = "meta" in data
record("T02 Response has pagination meta", status, has_meta, data)

items = data.get("data", []) if "data" in data else []
has_two = len(items) >= 2
record("T02 At least 2 variants returned", status, has_two, data)

if items:
    first = items[0]
    has_fields = all(k in first for k in ["variant_id", "variant_name", "product_id", "product_name", "stock_quantity", "low_stock_alert", "is_low_stock"])
    record("T02 VariantStockOut has all required fields", status, has_fields, first)
else:
    record("T02 VariantStockOut has all required fields", status, False, data)

# ── T03: Stock STOCK_IN (add) ─────────────────────────────────────
section("T03  POST /inventory/adjust — STOCK_IN (add stock)")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{
        "variant_id": VARIANT_A_ID,
        "quantity_change": 20,
        "type": "STOCK_IN",
        "reason": "Restocking from supplier",
    }]
}, expected=200)
record("T03 STOCK_IN +20 -> 200", status, passed, data)

# Verify stock updated to 70
status2, data2, passed2 = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
items2 = data2.get("data", [])
new_stock = items2[0]["stock_quantity"] if items2 else -1
record("T03 Stock updated: 50 + 20 = 70", status2, new_stock == 70, data2)

# ── T04: Stock STOCK_OUT (remove) ────────────────────────────────
section("T04  POST /inventory/adjust — STOCK_OUT (remove stock)")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{
        "variant_id": VARIANT_A_ID,
        "quantity_change": -10,
        "type": "STOCK_OUT",
        "reason": "Damaged goods",
    }]
}, expected=200)
record("T04 STOCK_OUT -10 -> 200", status, passed, data)

status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
items2 = data2.get("data", [])
new_stock = items2[0]["stock_quantity"] if items2 else -1
record("T04 Stock updated: 70 - 10 = 60", status2, new_stock == 60, data2)

# ── T05: Stock ADJUSTMENT ────────────────────────────────────────
section("T05  POST /inventory/adjust — ADJUSTMENT (inventory count)")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{
        "variant_id": VARIANT_B_ID,
        "quantity_change": -5,
        "type": "ADJUSTMENT",
        "reason": "Physical count discrepancy",
    }]
}, expected=200)
record("T05 ADJUSTMENT -5 -> 200", status, passed, data)

status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_B_ID}", token=TOKEN_A, expected=200)
items2 = data2.get("data", [])
new_stock = items2[0]["stock_quantity"] if items2 else -1
record("T05 Stock updated: 20 - 5 = 15", status2, new_stock == 15, data2)

# ── T06: Bulk adjustment ─────────────────────────────────────────
section("T06  POST /inventory/adjust — bulk (multiple variants)")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [
        {"variant_id": VARIANT_A_ID, "quantity_change": 5, "type": "STOCK_IN"},
        {"variant_id": VARIANT_B_ID, "quantity_change": 5, "type": "STOCK_IN"},
    ]
}, expected=200)
record("T06 Bulk adjust 2 variants -> 200", status, passed, data)

logs_returned = data.get("data", []) if "data" in data else []
record("T06 Response contains 2 log entries", status, len(logs_returned) == 2, data)

# Verify both stocks updated
status2, data2, _ = req("GET", INV, token=TOKEN_A, expected=200)
all_items = data2.get("data", []) if "data" in data2 else []
stock_map = {i["variant_id"]: i["stock_quantity"] for i in all_items}
record("T06 Variant A stock: 60 + 5 = 65", status2, stock_map.get(VARIANT_A_ID) == 65, stock_map)
record("T06 Variant B stock: 15 + 5 = 20", status2, stock_map.get(VARIANT_B_ID) == 20, stock_map)

# ── T07: Negative stock protection ───────────────────────────────
section("T07  POST /inventory/adjust — negative stock protection")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{
        "variant_id": VARIANT_B_ID,
        "quantity_change": -9999,
        "type": "STOCK_OUT",
    }]
}, expected=400)
record("T07 Over-deduct -> 400", status, passed, data)

# Verify stock NOT changed after rejection
status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_B_ID}", token=TOKEN_A, expected=200)
items2 = data2.get("data", [])
unchanged = items2[0]["stock_quantity"] == 20 if items2 else False
record("T07 Stock unchanged after rejection", status2, unchanged, data2)

# ── T08: Zero quantity_change rejected ───────────────────────────
section("T08  POST /inventory/adjust — zero quantity_change rejected")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": VARIANT_A_ID, "quantity_change": 0, "type": "ADJUSTMENT"}]
}, expected=422)
record("T08 quantity_change=0 -> 422 Unprocessable", status, passed, data)

# ── T09: Unknown variant ─────────────────────────────────────────
section("T09  POST /inventory/adjust — unknown variant")

status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": str(uuid.uuid4()), "quantity_change": 10}]
}, expected=404)
record("T09 Unknown variant -> 404", status, passed, data)

# ── T10: Bulk atomicity (one fails, all roll back) ────────────────
section("T10  POST /inventory/adjust — atomic rollback on partial failure")

# Check current stock of A before atomic test
status0, data0, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
before_stock_a = (data0.get("data") or [{}])[0].get("stock_quantity", -1)

# First item valid (+1), second item will fail (−9999 on B which has only 20)
status, data, _ = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [
        {"variant_id": VARIANT_A_ID, "quantity_change": 1, "type": "STOCK_IN"},
        {"variant_id": VARIANT_B_ID, "quantity_change": -9999, "type": "STOCK_OUT"},
    ]
}, expected=400)
record("T10 Batch with 2nd item invalid -> 400", status, status == 400, data)

# A's stock must be unchanged (first item rolled back)
status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
after_stock_a = (data2.get("data") or [{}])[0].get("stock_quantity", -1)
record("T10 Variant A stock unchanged (atomic rollback)", status2, after_stock_a == before_stock_a, data2)

# ── T11: Variant on deleted product rejected ──────────────────────
section("T11  POST /inventory/adjust — variant on soft-deleted product")

# Create a product, get variant, delete product, then try to adjust
status, data, _ = req("POST", PROD, token=TOKEN_A, body={
    "name": "Temp Delete Test",
    "category": "CLOTHING",
    "base_price": 80,
    "variants": [{"name": "Only", "sku": f"DEL-{sku_prefix}", "stock_quantity": 10}],
}, expected=201)
del_product_id = data.get("data", {}).get("id")
_, del_detail, _ = req("GET", f"{PROD}/{del_product_id}", token=TOKEN_A, expected=200)
del_variant_id = (del_detail.get("data", {}).get("variants") or [{}])[0].get("id")

# Soft-delete the product
req("DELETE", f"{PROD}/{del_product_id}", token=TOKEN_A, expected=204)

# Now try to adjust the variant — should 404 (product is inactive)
status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": del_variant_id, "quantity_change": 5}]
}, expected=404)
record("T11 Adjust variant of deleted product -> 404", status, passed, data)

# ── T12: Merchant isolation ──────────────────────────────────────
section("T12  Merchant isolation")

# Merchant A cannot adjust Merchant B's variant
status, data, passed = req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": MB_VARIANT_ID, "quantity_change": 100}]
}, expected=404)
record("T12 Merchant A cannot adjust Merchant B variant -> 404", status, passed, data)

# Merchant A's list doesn't include Merchant B's variants
status, data, _ = req("GET", INV, token=TOKEN_A, expected=200)
all_ids = [i["variant_id"] for i in (data.get("data") or [])]
record("T12 Merchant A's list excludes Merchant B variants", status, MB_VARIANT_ID not in all_ids, all_ids)

# Merchant B's list doesn't include Merchant A's variants
status, data, _ = req("GET", INV, token=TOKEN_B, expected=200)
all_ids_b = [i["variant_id"] for i in (data.get("data") or [])]
record("T12 Merchant B's list excludes Merchant A variants", status, VARIANT_A_ID not in all_ids_b, all_ids_b)

# ── T13: Inventory history / logs ────────────────────────────────
section("T13  GET /inventory/logs — inventory history")

status, data, passed = req("GET", f"{INV}/logs", token=TOKEN_A, expected=200)
record("T13 GET /inventory/logs -> 200", status, passed, data)

logs = data.get("data", []) if "data" in data else []
has_logs = len(logs) > 0
record("T13 Logs contain entries from prior adjustments", status, has_logs, data)

if logs:
    log = logs[0]
    has_log_fields = all(k in log for k in ["id", "merchant_id", "variant_id", "type", "quantity_before", "quantity_change", "quantity_after", "created_at"])
    record("T13 Log entry has all required fields", status, has_log_fields, log)
else:
    record("T13 Log entry has all required fields", status, False, {})

# ── T14: Log pagination ──────────────────────────────────────────
section("T14  GET /inventory/logs — pagination")

status, data, passed = req("GET", f"{INV}/logs?page=1&limit=2", token=TOKEN_A, expected=200)
record("T14 GET /inventory/logs?limit=2 -> 200", status, passed, data)

meta = data.get("meta", {}) if "data" in data else {}
correct_limit = meta.get("limit") == 2
record("T14 Pagination meta limit=2", status, correct_limit, meta)

logs_page = data.get("data", []) if "data" in data else []
record("T14 At most 2 logs returned", status, len(logs_page) <= 2, len(logs_page))

# ── T15: Log filter by variant_id ───────────────────────────────
section("T15  GET /inventory/logs — filter by variant_id")

status, data, passed = req("GET", f"{INV}/logs?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
record("T15 Filter by variant_id -> 200", status, passed, data)

filtered_logs = data.get("data", []) if "data" in data else []
all_match = all(l["variant_id"] == VARIANT_A_ID for l in filtered_logs)
record("T15 All logs belong to Variant A", status, all_match and len(filtered_logs) > 0, filtered_logs)

# ── T16: Log filter by type ──────────────────────────────────────
section("T16  GET /inventory/logs — filter by type")

status, data, passed = req("GET", f"{INV}/logs?type=STOCK_IN", token=TOKEN_A, expected=200)
record("T16 Filter by type=STOCK_IN -> 200", status, passed, data)

type_logs = data.get("data", []) if "data" in data else []
all_stock_in = all(l["type"] == "STOCK_IN" for l in type_logs)
record("T16 All returned logs have type=STOCK_IN", status, all_stock_in and len(type_logs) > 0, type_logs)

# ── T17: Log order (most recent first) ──────────────────────────
section("T17  GET /inventory/logs — most recent first ordering")

status, data, _ = req("GET", f"{INV}/logs?limit=50", token=TOKEN_A, expected=200)
all_logs = data.get("data", []) if "data" in data else []
is_ordered = True
for i in range(len(all_logs) - 1):
    if all_logs[i]["created_at"] < all_logs[i + 1]["created_at"]:
        is_ordered = False
        break
record("T17 Logs ordered by created_at DESC", status, is_ordered or len(all_logs) <= 1, all_logs[:2])

# ── T18: Low stock alerts ────────────────────────────────────────
section("T18  GET /inventory/alerts — low stock")

# Reduce Variant B to 0 so it triggers alert (low_stock_alert=5)
req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": VARIANT_B_ID, "quantity_change": -20, "type": "STOCK_OUT"}]
}, expected=200)

status, data, passed = req("GET", f"{INV}/alerts", token=TOKEN_A, expected=200)
record("T18 GET /inventory/alerts -> 200", status, passed, data)

alerts = data.get("data", []) if "data" in data else []
has_b = any(a["variant_id"] == VARIANT_B_ID for a in alerts)
record("T18 Variant B (stock=0) appears in alerts", status, has_b, alerts)

all_low = all(a["is_low_stock"] for a in alerts)
record("T18 All alert entries have is_low_stock=True", status, all_low and len(alerts) > 0, alerts)

# Variant A (stock=65, alert=10) should NOT be in alerts
no_a = not any(a["variant_id"] == VARIANT_A_ID for a in alerts)
record("T18 Variant A (stock=65) is NOT in alerts", status, no_a, alerts)

# ── T19: Alerts isolation ────────────────────────────────────────
section("T19  GET /inventory/alerts — merchant isolation")

status, data, _ = req("GET", f"{INV}/alerts", token=TOKEN_B, expected=200)
b_alerts = data.get("data", []) if "data" in data else []
no_a_in_b = not any(a["variant_id"] in [VARIANT_A_ID, VARIANT_B_ID] for a in b_alerts)
record("T19 Merchant B alerts don't include Merchant A variants", status, no_a_in_b, b_alerts)

# ── T20: DB persistence ──────────────────────────────────────────
section("T20  DB persistence — stock survives across requests")

status, data, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
current_stock = (data.get("data") or [{}])[0].get("stock_quantity", -1)

# Adjust +3
req("POST", f"{INV}/adjust", token=TOKEN_A, body={
    "adjustments": [{"variant_id": VARIANT_A_ID, "quantity_change": 3}]
}, expected=200)

# Fetch again
status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
new_stock = (data2.get("data") or [{}])[0].get("stock_quantity", -1)
record("T20 Stock persists: current + 3 = new", status2, new_stock == current_stock + 3, {"before": current_stock, "after": new_stock})

# ── T21: Product/variant inventory sync ──────────────────────────
section("T21  Product/variant inventory sync")

# Get product detail — variant stock should match inventory listing
status, data, _ = req("GET", f"{PROD}/{PRODUCT_ID}", token=TOKEN_A, expected=200)
product_variants = data.get("data", {}).get("variants", [])
product_a_stock = next((v["stock_quantity"] for v in product_variants if v["id"] == VARIANT_A_ID), None)

status2, data2, _ = req("GET", f"{INV}?variant_id={VARIANT_A_ID}", token=TOKEN_A, expected=200)
inv_a_stock = (data2.get("data") or [{}])[0].get("stock_quantity", None)

record("T21 Product variant stock matches inventory listing", status, product_a_stock == inv_a_stock, {"product": product_a_stock, "inventory": inv_a_stock})

# ── Summary ──────────────────────────────────────────────────────
total = pass_count + fail_count
print(f"\n{'=' * 60}")
print(f"  QA RESULTS: {pass_count}/{total} PASS  |  {fail_count} FAIL")
print("=" * 60)
if fail_count:
    print("  STATUS: NEEDS REVIEW")
else:
    print("  STATUS: ALL PASS")
