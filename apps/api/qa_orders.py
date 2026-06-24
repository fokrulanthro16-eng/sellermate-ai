"""
Orders Module QA Script — live-server functional QA.
Start API server before running: uvicorn app.main:app --reload
"""

import json
import time
import uuid
import http.client

BASE_HOST = "127.0.0.1"
BASE_PORT = 8000
ORDERS = "/api/v1/orders"
AUTH   = "/api/v1/auth"
PRODS  = "/api/v1/products"
CUST   = "/api/v1/customers"
INV    = "/api/v1/inventory"

pass_count = 0
fail_count = 0

TOKEN_A = TOKEN_B = None
PRODUCT_ID = VARIANT_ID = CUSTOMER_ID = ORDER_ID = None


def req(method, path, *, token=None, body=None, expected=200):
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=15)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    conn.request(method, path, body=json.dumps(body) if body else None, headers=headers)
    resp = conn.getresponse()
    status = resp.status
    raw = resp.read()
    try:
        payload = json.loads(raw) if raw else {}
    except Exception:
        payload = {}
    conn.close()
    return status, payload, status == expected


def req_raw(method, path, *, token=None):
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
    extra = ""
    if payload and not passed:
        extra = f"\n         {json.dumps(payload)[:120]}"
    print(f"  {mark} {label} | HTTP {status}{extra}")


def section(title):
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


# ── SETUP ─────────────────────────────────────────────────────────
section("SETUP — register two merchants")

ts = str(int(time.time()))[-9:]
ts2 = str(int(time.time()) + 1)[-9:]
PA, PB = f"+8801{ts}", f"+8801{ts2}"
PASS = "SecurePass123!"

for label, phone, t in [("A", PA, ts), ("B", PB, ts2)]:
    for _ in range(3):
        s, d, _ = req("POST", f"{AUTH}/register", body={
            "email": f"qa_ord_{t}@example.com", "phone": phone,
            "password": PASS, "business_name": f"Ord Biz {label}",
            "owner_name": label, "business_type": "FASHION_CLOTHING",
        }, expected=201)
        if s in (201, 409): break
        if s == 429: time.sleep(12)

_, da, _ = req("POST", f"{AUTH}/login", body={"identifier": PA, "password": PASS})
TOKEN_A = da.get("data", {}).get("tokens", {}).get("access_token")

_, db, _ = req("POST", f"{AUTH}/login", body={"identifier": PB, "password": PASS})
TOKEN_B = db.get("data", {}).get("tokens", {}).get("access_token")
print(f"  Merchant A={'OK' if TOKEN_A else 'FAIL'}  |  Merchant B={'OK' if TOKEN_B else 'FAIL'}")

# Create product + variant for merchant A
status, data, _ = req("POST", PRODS, token=TOKEN_A, body={
    "name": "QA Order Product", "category": "CLOTHING", "base_price": "300.00",
    "variants": [{"name": "Blue L", "sku": f"QO-{ts}", "price": "300.00",
                  "stock_quantity": 100, "low_stock_alert": 5}],
}, expected=201)
pid = data.get("data", {}).get("id")
_, pd, _ = req("GET", f"{PRODS}/{pid}", token=TOKEN_A)
VARIANT_ID = pd.get("data", {}).get("variants", [{}])[0].get("id")
PRODUCT_ID = pid
print(f"  Product ID={PRODUCT_ID}  |  Variant ID={VARIANT_ID}")

# Create customer
status, data, _ = req("POST", CUST, token=TOKEN_A, body={
    "name": "QA Order Customer", "phone": f"+88013{ts}",
}, expected=201)
CUSTOMER_ID = data.get("data", {}).get("id")
print(f"  Customer ID={CUSTOMER_ID}")


# ── T01: JWT protection ───────────────────────────────────────────
section("T01  JWT protection — all 8 endpoints")
FAKE = "00000000-0000-0000-0000-000000000000"
endpoints = [
    ("GET",    ORDERS),
    ("POST",   ORDERS),
    ("GET",    f"{ORDERS}/export"),
    ("GET",    f"{ORDERS}/{FAKE}"),
    ("PATCH",  f"{ORDERS}/{FAKE}"),
    ("POST",   f"{ORDERS}/{FAKE}/status"),
    ("POST",   f"{ORDERS}/{FAKE}/payment"),
    ("DELETE", f"{ORDERS}/{FAKE}"),
]
all_401 = all(req(m, p, expected=401)[0] == 401 for m, p in endpoints)
record("T01 All 8 endpoints return 401 without token", 401 if all_401 else 0, all_401)


# ── T02: Create order ─────────────────────────────────────────────
section("T02  POST /orders — create order")
status, data, passed = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 2}],
    "discount_amount": "50", "shipping_cost": "60", "payment_method": "COD",
}, expected=201)
record("T02 POST /orders -> 201", status, passed, data)
order = data.get("data", {})
ORDER_ID = order.get("id")
record("T02 Order has ID", status, bool(ORDER_ID), order)
record("T02 Status=PENDING", status, order.get("status") == "PENDING", order)
record("T02 PaymentStatus=UNPAID", status, order.get("payment_status") == "UNPAID", order)
# Calculation: 300*2=600 subtotal, -50 discount, +60 shipping = 610
record("T02 subtotal=600", status, float(order.get("subtotal", 0)) == 600.0, order)
record("T02 total_amount=610", status, float(order.get("total_amount", 0)) == 610.0, order)
record("T02 due_amount=610", status, float(order.get("due_amount", 0)) == 610.0, order)
record("T02 order_number starts with SM-", status, order.get("order_number", "").startswith("SM-"), order)


# ── T03: Inventory deducted on create ─────────────────────────────
section("T03  Inventory deducted on order create")
_, inv_data, _ = req("GET", f"{INV}?variant_id={VARIANT_ID}", token=TOKEN_A)
stock = next((v["stock_quantity"] for v in inv_data.get("data", [])
              if v["variant_id"] == VARIANT_ID), None)
record("T03 Stock reduced by 2 (from 100 to 98)", 200, stock == 98, inv_data)


# ── T04: Get order ────────────────────────────────────────────────
section("T04  GET /orders/{id} — get with details")
status, data, passed = req("GET", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A, expected=200)
record("T04 GET /orders/{id} -> 200", status, passed, data)
od = data.get("data", {})
record("T04 Has items list", status, isinstance(od.get("items"), list), od)
record("T04 Has status_history", status, isinstance(od.get("status_history"), list), od)
record("T04 Items[0].quantity=2", status, od.get("items", [{}])[0].get("quantity") == 2, od)
record("T04 History has PENDING entry", status,
       any(h["status"] == "PENDING" for h in od.get("status_history", [])), od)


# ── T05: Update order ─────────────────────────────────────────────
section("T05  PATCH /orders/{id} — update delivery info")
status, data, passed = req("PATCH", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A, body={
    "courier_name": "Pathao", "tracking_number": "PTH-999",
    "delivery_address": "Dhaka, Bangladesh",
}, expected=200)
record("T05 PATCH /orders/{id} -> 200", status, passed, data)
d = data.get("data", {})
record("T05 courier_name updated", status, d.get("courier_name") == "Pathao", d)
record("T05 tracking_number updated", status, d.get("tracking_number") == "PTH-999", d)


# ── T06: Change status ────────────────────────────────────────────
section("T06  POST /orders/{id}/status — status transitions")
status, data, passed = req("POST", f"{ORDERS}/{ORDER_ID}/status", token=TOKEN_A,
                            body={"status": "CONFIRMED", "note": "Confirmed by QA"}, expected=200)
record("T06 PENDING->CONFIRMED -> 200", status, passed, data)
record("T06 status=CONFIRMED", status, data.get("data", {}).get("status") == "CONFIRMED", data)

status2, data2, passed2 = req("POST", f"{ORDERS}/{ORDER_ID}/status", token=TOKEN_A,
                               body={"status": "DELIVERED"}, expected=200)
record("T06 CONFIRMED->DELIVERED -> 200", status2, passed2, data2)

_, od2, _ = req("GET", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A)
record("T06 delivered_at set on DELIVERED", 200, od2.get("data", {}).get("delivered_at") is not None, od2)
hist = od2.get("data", {}).get("status_history", [])
record("T06 Status history has 3 entries (PENDING, CONFIRMED, DELIVERED)", 200,
       len(hist) >= 3, hist)
note_found = any(h.get("note") == "Confirmed by QA" for h in hist)
record("T06 Status note saved in history", 200, note_found, hist)


# ── T07: Terminal state guard ─────────────────────────────────────
section("T07  Terminal state guard (Bug 3 fix)")
# Create fresh order to cancel
_, tmp_data, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=201)
tmp_order_id = tmp_data.get("data", {}).get("id")
req("DELETE", f"{ORDERS}/{tmp_order_id}", token=TOKEN_A, expected=200)

status, data, passed = req("POST", f"{ORDERS}/{tmp_order_id}/status", token=TOKEN_A,
                             body={"status": "CONFIRMED"}, expected=400)
record("T07 Status change from CANCELLED -> 400 (terminal guard)", status, passed, data)


# ── T08: Record payment ───────────────────────────────────────────
section("T08  POST /orders/{id}/payment — record payment")
# Create fresh order for payment tests
_, po, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=201)
PAY_ORDER_ID = po.get("data", {}).get("id")
PAY_TOTAL = float(po.get("data", {}).get("total_amount", 300))

status, data, passed = req("POST", f"{ORDERS}/{PAY_ORDER_ID}/payment", token=TOKEN_A,
                             body={"amount": "100", "method": "BKASH"}, expected=200)
record("T08 Partial payment -> 200", status, passed, data)
d = data.get("data", {})
record("T08 payment_status=PARTIAL", status, d.get("payment_status") == "PARTIAL", d)
record("T08 paid_amount=100", status, float(d.get("paid_amount", 0)) == 100.0, d)
record("T08 due_amount=total-100", status, float(d.get("due_amount", 0)) == PAY_TOTAL - 100, d)

status2, data2, passed2 = req("POST", f"{ORDERS}/{PAY_ORDER_ID}/payment", token=TOKEN_A,
                               body={"amount": str(PAY_TOTAL - 100), "method": "BKASH"}, expected=200)
record("T08 Full payment -> 200", status2, passed2, data2)
record("T08 payment_status=PAID after full payment", status2,
       data2.get("data", {}).get("payment_status") == "PAID", data2)

# Overpayment
status3, data3, passed3 = req("POST", f"{ORDERS}/{PAY_ORDER_ID}/payment", token=TOKEN_A,
                               body={"amount": "999", "method": "COD"}, expected=400)
record("T08 Overpayment -> 400", status3, passed3, data3)


# ── T09: Payment on cancelled order ──────────────────────────────
section("T09  Payment on cancelled order (Bug 4 fix)")
_, co, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=201)
CANC_ORDER_ID = co.get("data", {}).get("id")
req("DELETE", f"{ORDERS}/{CANC_ORDER_ID}", token=TOKEN_A, expected=200)

status, data, passed = req("POST", f"{ORDERS}/{CANC_ORDER_ID}/payment", token=TOKEN_A,
                             body={"amount": "100", "method": "COD"}, expected=400)
record("T09 Payment on cancelled order -> 400", status, passed, data)


# ── T10: Cancel order + inventory restore ─────────────────────────
section("T10  DELETE /orders/{id} — cancel with inventory restore (Bug 1 fix)")
# Check current stock
_, inv, _ = req("GET", f"{INV}?variant_id={VARIANT_ID}", token=TOKEN_A)
stock_before = next((v["stock_quantity"] for v in inv.get("data", [])
                     if v["variant_id"] == VARIANT_ID), None)

_, new_order, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 5}],
}, expected=201)
NEW_ORDER_ID = new_order.get("data", {}).get("id")

_, inv2, _ = req("GET", f"{INV}?variant_id={VARIANT_ID}", token=TOKEN_A)
stock_after_create = next((v["stock_quantity"] for v in inv2.get("data", [])
                           if v["variant_id"] == VARIANT_ID), None)
record("T10 Stock deducted by 5 on create", 200, stock_after_create == stock_before - 5)

status, data, passed = req("DELETE", f"{ORDERS}/{NEW_ORDER_ID}", token=TOKEN_A, expected=200)
record("T10 Cancel -> 200", status, passed, data)
record("T10 Status=CANCELLED", status, data.get("data", {}).get("status") == "CANCELLED", data)

_, inv3, _ = req("GET", f"{INV}?variant_id={VARIANT_ID}", token=TOKEN_A)
stock_after_cancel = next((v["stock_quantity"] for v in inv3.get("data", [])
                           if v["variant_id"] == VARIANT_ID), None)
record("T10 Stock restored to pre-order level after cancel", 200,
       stock_after_cancel == stock_before)


# ── T11: Customer stats rollback on cancel ────────────────────────
section("T11  Customer stats rollback on cancel (Bug 2 fix)")
_, cdata_before, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A)
orders_before = cdata_before.get("data", {}).get("total_orders", 0)

_, stat_order, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=201)
STAT_ORDER_ID = stat_order.get("data", {}).get("id")

_, cdata_mid, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A)
orders_mid = cdata_mid.get("data", {}).get("total_orders", 0)
record("T11 Customer total_orders incremented on create", 200,
       orders_mid == orders_before + 1)

req("DELETE", f"{ORDERS}/{STAT_ORDER_ID}", token=TOKEN_A, expected=200)
_, cdata_after, _ = req("GET", f"{CUST}/{CUSTOMER_ID}", token=TOKEN_A)
orders_after = cdata_after.get("data", {}).get("total_orders", 0)
record("T11 Customer total_orders decremented on cancel", 200,
       orders_after == orders_before)


# ── T12: Cannot cancel shipped/delivered ──────────────────────────
section("T12  Cancel restrictions")
_, ro, _ = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=201)
R_OID = ro.get("data", {}).get("id")
req("POST", f"{ORDERS}/{R_OID}/status", token=TOKEN_A, body={"status": "SHIPPED"}, expected=200)
status, data, passed = req("DELETE", f"{ORDERS}/{R_OID}", token=TOKEN_A, expected=400)
record("T12 Cannot cancel SHIPPED order -> 400", status, passed, data)


# ── T13: List orders + filters ────────────────────────────────────
section("T13  GET /orders — list with filters")
status, data, passed = req("GET", ORDERS, token=TOKEN_A, expected=200)
record("T13 GET /orders -> 200", status, passed, data)
meta = data.get("meta", {})
record("T13 Has pagination meta", status, "total" in meta, meta)

status2, data2, _ = req("GET", f"{ORDERS}?status=PENDING", token=TOKEN_A, expected=200)
results = data2.get("data", [])
all_pending = all(o["status"] == "PENDING" for o in results)
record("T13 Status filter returns only PENDING", status2, all_pending or len(results) == 0, data2)

status3, data3, _ = req("GET", f"{ORDERS}?payment_status=UNPAID", token=TOKEN_A, expected=200)
results3 = data3.get("data", [])
all_unpaid = all(o["payment_status"] == "UNPAID" for o in results3)
record("T13 Payment status filter returns only UNPAID", status3, all_unpaid or len(results3) == 0, data3)

order_num = new_order.get("data", {}).get("order_number", "")
status4, data4, _ = req("GET", f"{ORDERS}?search={order_num[:8]}", token=TOKEN_A, expected=200)
record("T13 Search by order number finds result", status4,
       any(o.get("order_number") == order_num for o in data4.get("data", [])), data4)


# ── T14: CSV export ───────────────────────────────────────────────
section("T14  GET /orders/export — CSV download")
status, raw, ct = req_raw("GET", f"{ORDERS}/export", token=TOKEN_A)
record("T14 GET /orders/export -> 200", status, status == 200)
record("T14 Content-Type is text/csv", status, "text/csv" in ct)
csv_text = raw.decode("utf-8-sig", errors="replace")
record("T14 CSV has header row", status, "order_number" in csv_text.lower())
record("T14 Export requires auth", 401, req_raw("GET", f"{ORDERS}/export")[0] == 401)


# ── T15: Merchant isolation ───────────────────────────────────────
section("T15  Merchant isolation")
# T15a: B cannot see A's orders
_, b_list, _ = req("GET", ORDERS, token=TOKEN_B, expected=200)
b_ids = [o["id"] for o in b_list.get("data", [])]
record("T15 Merchant B list excludes Merchant A's orders", 200, ORDER_ID not in b_ids)

# T15b: B cannot GET A's order
status, data, passed = req("GET", f"{ORDERS}/{ORDER_ID}", token=TOKEN_B, expected=404)
record("T15 Merchant B cannot GET Merchant A's order -> 404", status, passed, data)

# T15c: B cannot PATCH A's order
status, data, passed = req("PATCH", f"{ORDERS}/{ORDER_ID}", token=TOKEN_B, body={}, expected=404)
record("T15 Merchant B cannot PATCH Merchant A's order -> 404", status, passed, data)

# T15d: B cannot cancel A's order
status, data, passed = req("DELETE", f"{ORDERS}/{ORDER_ID}", token=TOKEN_B, expected=404)
record("T15 Merchant B cannot cancel Merchant A's order -> 404", status, passed, data)

# T15e: Cross-merchant customer usage rejected
_, mbc, _ = req("POST", CUST, token=TOKEN_B, body={
    "name": "MB Customer", "phone": f"+88014{ts}",
}, expected=201)
MB_CID = mbc.get("data", {}).get("id")
status, data, passed = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": MB_CID,
    "items": [{"product_id": PRODUCT_ID, "variant_id": VARIANT_ID, "quantity": 1}],
}, expected=404)
record("T15 Cross-merchant customer use rejected -> 404", status, passed, data)


# ── T16: Validation errors ────────────────────────────────────────
section("T16  Validation errors")
status, data, passed = req("POST", ORDERS, token=TOKEN_A, body={
    "customer_id": CUSTOMER_ID, "items": [],
}, expected=422)
record("T16 Empty items -> 422", status, passed, data)

status2, data2, passed2 = req("POST", f"{ORDERS}/{ORDER_ID}/payment", token=TOKEN_A,
                               body={"amount": "0", "method": "COD"}, expected=422)
record("T16 Payment amount=0 -> 422", status2, passed2, data2)


# ── T17: DB persistence ───────────────────────────────────────────
section("T17  DB persistence")
_, pdata, _ = req("GET", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A)
record("T17 Order persists across requests", 200,
       pdata.get("data", {}).get("id") == ORDER_ID)

req("PATCH", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A,
    body={"internal_notes": "persisted note"}, expected=200)
_, pdata2, _ = req("GET", f"{ORDERS}/{ORDER_ID}", token=TOKEN_A)
record("T17 PATCH persists to DB", 200,
       pdata2.get("data", {}).get("internal_notes") == "persisted note")


# ── Summary ──────────────────────────────────────────────────────
total = pass_count + fail_count
print(f"\n{'=' * 60}")
print(f"  QA RESULTS: {pass_count}/{total} PASS  |  {fail_count} FAIL")
print("=" * 60)
print("  STATUS:", "ALL PASS" if fail_count == 0 else "NEEDS REVIEW")
