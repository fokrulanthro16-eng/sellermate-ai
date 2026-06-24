"""Product Module QA — all 9 endpoints, security, isolation, pagination."""
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE    = "http://localhost:8000"
AUTH    = "/api/v1/auth"
PROD    = "/api/v1/products"


# ── helpers ───────────────────────────────────────────────────────────────────

def req(method, path, body=None, token=None, expected=None, params=None):
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            status = resp.status
            raw = resp.read()
            payload = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read()
            payload = json.loads(raw) if raw else {}
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


# ── setup: two merchants ───────────────────────────────────────────────────────
sep("SETUP — registering two merchants")
ts = str(int(time.time()))[-9:]
ts2 = str(int(time.time()) + 1)[-9:]

PHONE_A = f"+8801{ts}"
PHONE_B = f"+8801{ts2}"

_, r, _ = req("POST", f"{AUTH}/register", {
    "email": f"prodqa_a_{ts}@example.com", "phone": PHONE_A,
    "password": "ProdQA123!", "business_name": "Product QA Shop A",
    "owner_name": "Merchant A", "business_type": "ELECTRONICS",
}, expected=201)
TOKEN_A = r.get("data", {}).get("tokens", {}).get("access_token", "")
print(f"  Merchant A: {PHONE_A}  token={'OK' if TOKEN_A else 'FAIL'}")

_, r, _ = req("POST", f"{AUTH}/register", {
    "email": f"prodqa_b_{ts2}@example.com", "phone": PHONE_B,
    "password": "ProdQA123!", "business_name": "Product QA Shop B",
    "owner_name": "Merchant B", "business_type": "FASHION_CLOTHING",
}, expected=201)
TOKEN_B = r.get("data", {}).get("tokens", {}).get("access_token", "")
print(f"  Merchant B: {PHONE_B}  token={'OK' if TOKEN_B else 'FAIL'}")

if not TOKEN_A or not TOKEN_B:
    print("  [FATAL] Could not obtain tokens. Aborting.")
    sys.exit(1)


# ── T01: JWT protection ───────────────────────────────────────────────────────
sep("T01  JWT protection (no token)")
jwt_cases = [
    ("GET",    f"{PROD}",             None),
    ("POST",   f"{PROD}",             {"name": "x", "category": "y", "base_price": 100}),
    ("GET",    f"{PROD}/categories",  None),
    ("GET",    f"{PROD}/fake-id",     None),
    ("PATCH",  f"{PROD}/fake-id",     {"name": "x"}),
    ("DELETE", f"{PROD}/fake-id",     None),
    ("POST",   f"{PROD}/fake-id/variants", {"name": "v", "stock_quantity": 0}),
    ("PATCH",  f"{PROD}/fake-id/variants/fake-vid", {"name": "v"}),
    ("DELETE", f"{PROD}/fake-id/variants/fake-vid", None),
]
all_401 = True
for method, path, body in jwt_cases:
    s, _, _ = req(method, path, body)
    if s != 401:
        all_401 = False
        print(f"  WARNING: {method} {path} returned {s}, expected 401")
record("T01 All 9 product endpoints return 401 without token", 401, all_401)


# ── T02: Create product (minimal) ─────────────────────────────────────────────
sep("T02  POST /products — create minimal product")
status, payload, passed = req("POST", PROD, {
    "name": "Test Widget",
    "category": "Electronics",
    "base_price": 500,
}, token=TOKEN_A, expected=201)
record("T02 POST /products -> 201", status, passed, payload)
p_data = payload.get("data", {})
PRODUCT_ID = p_data.get("id", "")
has_fields = all(k in p_data for k in ["id", "merchant_id", "name", "category", "base_price",
                                        "is_active", "is_published", "total_sold", "variants_count" if "variants_count" in p_data else "id"])
record("T02 Product response has required fields", status, "id" in p_data and "merchant_id" in p_data)
record("T02 is_active=True by default", status, p_data.get("is_active") is True)
record("T02 is_published=False by default", status, p_data.get("is_published") is False)
record("T02 total_sold=0 by default", status, p_data.get("total_sold") == 0)
print(f"         Product ID: {PRODUCT_ID}")


# ── T03: Create product with variants ─────────────────────────────────────────
sep("T03  POST /products — create with variants")
status, payload, passed = req("POST", PROD, {
    "name": "T-Shirt Pro",
    "name_bangla": "টি-শার্ট প্রো",
    "description": "Best t-shirt",
    "category": "Fashion",
    "sku": f"TSHIRT-{ts}",
    "base_price": 350,
    "sale_price": 299,
    "variants": [
        {"name": "Small Red", "attributes": {"size": "S", "color": "Red"}, "stock_quantity": 10, "low_stock_alert": 3},
        {"name": "Large Blue", "attributes": {"size": "L", "color": "Blue"}, "stock_quantity": 5, "sku": f"TSHIRT-{ts}-LB"},
    ],
}, token=TOKEN_A, expected=201)
record("T03 POST /products with variants -> 201", status, passed, payload)
PRODUCT_ID_2 = payload.get("data", {}).get("id", "")
record("T03 SKU stored correctly", status, payload.get("data", {}).get("sku") == f"TSHIRT-{ts}")


# ── T04: Duplicate SKU → 409 ──────────────────────────────────────────────────
sep("T04  POST /products — duplicate SKU")
status, payload, passed = req("POST", PROD, {
    "name": "Duplicate SKU Product",
    "category": "Fashion",
    "sku": f"TSHIRT-{ts}",
    "base_price": 100,
}, token=TOKEN_A, expected=409)
record("T04 POST /products duplicate SKU -> 409", status, passed, payload)


# ── T05: List products (pagination) ───────────────────────────────────────────
sep("T05  GET /products — list with pagination")
status, payload, passed = req("GET", PROD, token=TOKEN_A, expected=200)
record("T05 GET /products -> 200", status, passed, payload)
meta = payload.get("meta", {})
has_meta = all(k in meta for k in ["page", "limit", "total", "total_pages"])
record("T05 Response has pagination meta", status, has_meta)
record("T05 total >= 2 (at least 2 products created)", status, meta.get("total", 0) >= 2)
record("T05 default page=1, limit=20", status, meta.get("page") == 1 and meta.get("limit") == 20)

# Custom pagination
status, payload, passed = req("GET", PROD, token=TOKEN_A, params={"page": "1", "limit": "1"}, expected=200)
record("T05 Pagination limit=1 works", status, passed and len(payload.get("data", [])) == 1)


# ── T06: Search ───────────────────────────────────────────────────────────────
sep("T06  GET /products — search")
status, payload, passed = req("GET", PROD, token=TOKEN_A, params={"search": "Widget"}, expected=200)
record("T06 Search by name -> 200", status, passed)
found_widget = any("Widget" in p.get("name", "") for p in payload.get("data", []))
record("T06 Search returns matching product", status, found_widget)

status, payload, passed = req("GET", PROD, token=TOKEN_A, params={"search": "nonexistent_xyz_abc"}, expected=200)
record("T06 Search for nonexistent -> 200 with empty data", status, passed and payload.get("data") == [])


# ── T07: Category filter ──────────────────────────────────────────────────────
sep("T07  GET /products — category filter")
status, payload, passed = req("GET", PROD, token=TOKEN_A, params={"category": "Electronics"}, expected=200)
record("T07 Category filter -> 200", status, passed)
all_electronics = all(p.get("category") == "Electronics" for p in payload.get("data", []))
record("T07 All returned products match category", status, all_electronics)


# ── T08: Get product by ID (with variants) ────────────────────────────────────
sep("T08  GET /products/{id} — product detail with variants")
status, payload, passed = req("GET", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_A, expected=200)
record("T08 GET /products/{id} -> 200", status, passed, payload)
prod_detail = payload.get("data", {})
record("T08 Response includes variants list", status, "variants" in prod_detail)
record("T08 Two variants returned", status, len(prod_detail.get("variants", [])) == 2)
if prod_detail.get("variants"):
    v0 = prod_detail["variants"][0]
    record("T08 Variant has required fields", status, all(k in v0 for k in
           ["id", "product_id", "name", "attributes", "stock_quantity", "low_stock_alert"]))

VARIANT_ID = prod_detail.get("variants", [{}])[0].get("id", "") if prod_detail.get("variants") else ""


# ── T09: Get non-existent product → 404 ──────────────────────────────────────
sep("T09  GET /products/{id} — not found")
status, payload, passed = req("GET", f"{PROD}/00000000-0000-0000-0000-000000000000",
                               token=TOKEN_A, expected=404)
record("T09 GET /products/nonexistent -> 404", status, passed, payload)


# ── T10: Update product ───────────────────────────────────────────────────────
sep("T10  PATCH /products/{id} — update")
status, payload, passed = req("PATCH", f"{PROD}/{PRODUCT_ID}", {
    "name": "Updated Widget",
    "description": "Now with more description",
    "sale_price": 449,
    "is_published": True,
}, token=TOKEN_A, expected=200)
record("T10 PATCH /products/{id} -> 200", status, passed, payload)
updated = payload.get("data", {})
record("T10 name updated", status, updated.get("name") == "Updated Widget")
record("T10 sale_price updated", status, str(updated.get("sale_price", "")) in ["449", "449.00"])
record("T10 is_published updated to True", status, updated.get("is_published") is True)


# ── T11: Variant operations ───────────────────────────────────────────────────
sep("T11  Variant CRUD on /products/{id}/variants")

# Add variant
status, payload, passed = req("POST", f"{PROD}/{PRODUCT_ID}/variants", {
    "name": "Blue Version",
    "attributes": {"color": "Blue"},
    "stock_quantity": 25,
    "low_stock_alert": 5,
    "price": 480,
}, token=TOKEN_A, expected=201)
record("T11 POST /variants -> 201", status, passed, payload)
NEW_VARIANT_ID = payload.get("data", {}).get("id", "")
record("T11 Variant has correct product_id", status,
       payload.get("data", {}).get("product_id") == PRODUCT_ID)
record("T11 Variant stock_quantity correct", status,
       payload.get("data", {}).get("stock_quantity") == 25)

# Update variant
if NEW_VARIANT_ID:
    status, payload, passed = req("PATCH", f"{PROD}/{PRODUCT_ID}/variants/{NEW_VARIANT_ID}", {
        "stock_quantity": 30,
        "name": "Blue Version XL",
    }, token=TOKEN_A, expected=200)
    record("T11 PATCH /variants/{id} -> 200", status, passed)
    record("T11 Variant name updated", status, payload.get("data", {}).get("name") == "Blue Version XL")
    record("T11 Variant stock_quantity updated", status, payload.get("data", {}).get("stock_quantity") == 30)

# Delete variant
if NEW_VARIANT_ID:
    status, payload, passed = req("DELETE", f"{PROD}/{PRODUCT_ID}/variants/{NEW_VARIANT_ID}",
                                   token=TOKEN_A, expected=204)
    record("T11 DELETE /variants/{id} -> 204", status, passed)

    # Verify deletion by getting product
    status, detail, _ = req("GET", f"{PROD}/{PRODUCT_ID}", token=TOKEN_A)
    variant_ids = [v["id"] for v in detail.get("data", {}).get("variants", [])]
    record("T11 Deleted variant not in product variants", status, NEW_VARIANT_ID not in variant_ids)


# ── T12: Get categories ───────────────────────────────────────────────────────
sep("T12  GET /products/categories")
status, payload, passed = req("GET", f"{PROD}/categories", token=TOKEN_A, expected=200)
record("T12 GET /categories -> 200", status, passed, payload)
cats = payload.get("data", [])
record("T12 Returns list of strings", status, isinstance(cats, list) and all(isinstance(c, str) for c in cats))
record("T12 'Electronics' and 'Fashion' in categories", status,
       "Electronics" in cats and "Fashion" in cats)


# ── T13: Soft delete ─────────────────────────────────────────────────────────
sep("T13  DELETE /products/{id} — soft delete")
status, payload, passed = req("DELETE", f"{PROD}/{PRODUCT_ID}", token=TOKEN_A, expected=204)
record("T13 DELETE /products/{id} -> 204", status, passed)

# Verify: GET should return 404 after delete
status, payload, passed = req("GET", f"{PROD}/{PRODUCT_ID}", token=TOKEN_A, expected=404)
record("T13 GET deleted product -> 404", status, passed, payload)

# Verify: PATCH should return 404 after delete
status, payload, passed = req("PATCH", f"{PROD}/{PRODUCT_ID}", {"name": "Ghost"}, token=TOKEN_A, expected=404)
record("T13 PATCH deleted product -> 404 (bug fix)", status, passed, payload)

# Verify: POST variant on deleted product -> 404
status, payload, passed = req("POST", f"{PROD}/{PRODUCT_ID}/variants",
                               {"name": "Ghost Variant", "stock_quantity": 0},
                               token=TOKEN_A, expected=404)
record("T13 POST variant on deleted product -> 404 (bug fix)", status, passed, payload)

# Verify: not in list (is_active filter)
status, list_resp, _ = req("GET", PROD, token=TOKEN_A)
ids = [p["id"] for p in list_resp.get("data", [])]
record("T13 Deleted product not in list (default is_active filter)", status, PRODUCT_ID not in ids)


# ── T14: Merchant isolation ───────────────────────────────────────────────────
sep("T14  Merchant isolation — Merchant B cannot access Merchant A's products")

# Merchant B tries to read Merchant A's product
status, payload, passed = req("GET", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_B, expected=404)
record("T14 Merchant B GET Merchant A's product -> 404", status, passed, payload)

# Merchant B tries to update Merchant A's product
status, payload, passed = req("PATCH", f"{PROD}/{PRODUCT_ID_2}", {"name": "Hijacked"},
                               token=TOKEN_B, expected=404)
record("T14 Merchant B PATCH Merchant A's product -> 404", status, passed, payload)

# Merchant B tries to delete Merchant A's product
status, payload, passed = req("DELETE", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_B, expected=404)
record("T14 Merchant B DELETE Merchant A's product -> 404", status, passed, payload)

# Merchant B tries to add variant to Merchant A's product
status, payload, passed = req("POST", f"{PROD}/{PRODUCT_ID_2}/variants",
                               {"name": "Injected Variant", "stock_quantity": 0},
                               token=TOKEN_B, expected=404)
record("T14 Merchant B POST variant on Merchant A's product -> 404", status, passed, payload)

# Verify Merchant A's product is unmodified (name not changed to "Hijacked")
status, detail, _ = req("GET", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_A)
record("T14 Merchant A's product name unchanged after isolation tests", status,
       detail.get("data", {}).get("name") == "T-Shirt Pro")


# ── T15: Inventory linkage — variant stock tracking ───────────────────────────
sep("T15  Inventory linkage — variant stock reflects on GET")
# Add variant with known stock
status, payload, passed = req("POST", f"{PROD}/{PRODUCT_ID_2}/variants", {
    "name": "Inventory Test Variant",
    "attributes": {"size": "M"},
    "stock_quantity": 50,
    "low_stock_alert": 10,
}, token=TOKEN_A, expected=201)
record("T15 Add variant with stock=50 -> 201", status, passed)
INV_VARIANT_ID = payload.get("data", {}).get("id", "")
stock_on_create = payload.get("data", {}).get("stock_quantity", -1)
record("T15 stock_quantity=50 on creation", status, stock_on_create == 50)

# Update stock via PATCH variant
if INV_VARIANT_ID:
    status, payload, passed = req("PATCH", f"{PROD}/{PRODUCT_ID_2}/variants/{INV_VARIANT_ID}",
                                   {"stock_quantity": 35}, token=TOKEN_A, expected=200)
    record("T15 Update stock to 35 -> 200", status, passed)
    record("T15 stock_quantity=35 after update", status, payload.get("data", {}).get("stock_quantity") == 35)

    # Verify via full product GET
    status, detail, _ = req("GET", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_A)
    inv_variant = next((v for v in detail.get("data", {}).get("variants", []) if v["id"] == INV_VARIANT_ID), None)
    record("T15 Stock change persisted on full GET", status, inv_variant and inv_variant.get("stock_quantity") == 35)


# ── T16: DB persistence (cross-request) ──────────────────────────────────────
sep("T16  DB persistence — data survives across requests")
# Re-read the product and verify all fields from T03 are still correct
status, payload, passed = req("GET", f"{PROD}/{PRODUCT_ID_2}", token=TOKEN_A, expected=200)
record("T16 Product still exists after multiple requests", status, passed)
p = payload.get("data", {})
record("T16 name_bangla persisted", status, p.get("name_bangla") == "টি-শার্ট প্রো")
record("T16 description persisted", status, p.get("description") == "Best t-shirt")
record("T16 sale_price persisted", status, str(p.get("sale_price", "")) in ["299", "299.00"])


# ── T17: is_active filter explicit ───────────────────────────────────────────
sep("T17  is_active filter")
# When is_active=false passed explicitly, deleted products should appear
status, payload, passed = req("GET", PROD, token=TOKEN_A, params={"is_active": "false"}, expected=200)
record("T17 GET /products?is_active=false -> 200", status, passed)
has_deleted = any(p["id"] == PRODUCT_ID for p in payload.get("data", []))
record("T17 Deleted product visible with is_active=false", status, has_deleted)


# ── Summary ───────────────────────────────────────────────────────────────────
sep("RESULTS")
total    = len(results)
passed_n = sum(1 for _, _, p in results if p)
failed_n = total - passed_n

for name, sc, p in results:
    print(f"  [{'PASS' if p else 'FAIL'}] {name}")

print(f"\n  Total: {total}  |  Passed: {passed_n}  |  Failed: {failed_n}")
if failed_n == 0:
    print("\n  PRODUCT QA: ALL PASS")
else:
    print(f"\n  PRODUCT QA: {failed_n} FAILURE(S)")
    sys.exit(1)
