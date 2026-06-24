# Product Module QA Report
**Date:** 2026-06-21  
**Status:** ALL PASS ✓  
**QA Score:** 60/60 live checks | 33/33 pytest | 0 failures

---

## Endpoints Tested

| Method | Path | Purpose | Result |
|--------|------|---------|--------|
| `GET` | `/api/v1/products` | List with pagination, search, filter | PASS |
| `POST` | `/api/v1/products` | Create product (minimal + with variants) | PASS |
| `GET` | `/api/v1/products/categories` | Get distinct categories | PASS |
| `GET` | `/api/v1/products/{id}` | Product detail with variants | PASS |
| `PATCH` | `/api/v1/products/{id}` | Partial update | PASS |
| `DELETE` | `/api/v1/products/{id}` | Soft delete (204 No Content) | PASS |
| `POST` | `/api/v1/products/{id}/variants` | Add variant | PASS |
| `PATCH` | `/api/v1/products/{id}/variants/{vid}` | Update variant | PASS |
| `DELETE` | `/api/v1/products/{id}/variants/{vid}` | Hard delete variant | PASS |

---

## Bugs Found and Fixed

### Bug 1 — `update_product` allowed patching soft-deleted products
**Severity:** HIGH  
**File:** `app/services/product_service.py`  
**Description:** `update_product` queried without an `is_active` filter. A merchant could PATCH a product they had soft-deleted and receive 200 instead of 404.  
**Fix:** Added `Product.is_active.is_(True)` to the WHERE clause in `update_product`.

```python
# Before (buggy):
select(Product).where(Product.merchant_id == merchant_id, Product.id == product_id)

# After (fixed):
select(Product).where(
    Product.merchant_id == merchant_id,
    Product.id == product_id,
    Product.is_active.is_(True),
)
```

---

### Bug 2 — `add_variant` allowed adding variants to deleted products
**Severity:** HIGH  
**File:** `app/services/product_service.py`  
**Description:** Parent product lookup in `add_variant` had no `is_active` filter. A merchant could `POST /products/{id}/variants` on a soft-deleted product and get 201.  
**Fix:** Added `Product.is_active.is_(True)` to the parent product check in `add_variant`.

---

### Bug 3 — `update_variant` and `delete_variant` operated on deleted products' variants
**Severity:** MEDIUM  
**File:** `app/services/product_service.py`  
**Description:** Both functions join `Product` but did not check `Product.is_active`. Variants belonging to a soft-deleted product could still be modified or hard-deleted directly.  
**Fix:** Added `Product.is_active.is_(True)` to the WHERE clause in both `update_variant` and `delete_variant`.

---

### Bug 4 — `create_product` SKU conflict caused 500 on DB race condition
**Severity:** MEDIUM  
**File:** `app/services/product_service.py`  
**Description:** The pre-check for duplicate SKU is vulnerable to TOCTOU: two concurrent requests with the same SKU could both pass the select check, then the DB unique constraint fires and raises `IntegrityError`, which becomes an unhandled 500.  
**Fix:** Wrapped the initial `flush()` in `try/except IntegrityError` to catch the DB-level constraint and re-raise as `ConflictException` (409).

```python
try:
    await db.flush()
except IntegrityError:
    await db.rollback()
    raise ConflictException(f"SKU '{data.sku}' already exists")
```

---

## Security Results

| Test | Expected | Result |
|------|----------|--------|
| `GET /products` — no token | 401 | PASS |
| `POST /products` — no token | 401 | PASS |
| `GET /products/categories` — no token | 401 | PASS |
| `GET /products/{id}` — no token | 401 | PASS |
| `PATCH /products/{id}` — no token | 401 | PASS |
| `DELETE /products/{id}` — no token | 401 | PASS |
| `POST /products/{id}/variants` — no token | 401 | PASS |
| `PATCH /products/{id}/variants/{vid}` — no token | 401 | PASS |
| `DELETE /products/{id}/variants/{vid}` — no token | 401 | PASS |
| Merchant B GET Merchant A's product | 404 | PASS |
| Merchant B PATCH Merchant A's product | 404 | PASS |
| Merchant B DELETE Merchant A's product | 404 | PASS |
| Merchant B POST variant on Merchant A's product | 404 | PASS |
| Merchant A's product unmodified after isolation attack | verified | PASS |
| Merchant B's list contains only own products | verified | PASS |

**Security verdict:** All 9 endpoints correctly require JWT. All cross-merchant access attempts are rejected with 404 (intentionally not 403, to avoid revealing resource existence).

---

## Functional Test Results — Live QA (60 checks)

| Section | Checks | Result |
|---------|--------|--------|
| T01 JWT protection (all 9 endpoints) | 1 | PASS |
| T02 Create product minimal | 5 | PASS |
| T03 Create product with inline variants | 2 | PASS |
| T04 Duplicate SKU → 409 | 1 | PASS |
| T05 List products + pagination | 5 | PASS |
| T06 Search (name match + no match) | 3 | PASS |
| T07 Category filter | 2 | PASS |
| T08 Get by ID with variants | 4 | PASS |
| T09 Not found → 404 | 1 | PASS |
| T10 Update product | 4 | PASS |
| T11 Variant CRUD (add/update/delete) | 8 | PASS |
| T12 Categories endpoint | 3 | PASS |
| T13 Soft delete + bug fix verification | 5 | PASS |
| T14 Merchant isolation (4 attack vectors) | 5 | PASS |
| T15 Inventory/stock linkage | 5 | PASS |
| T16 DB persistence across requests | 4 | PASS |
| T17 is_active explicit filter | 2 | PASS |
| **Total** | **60** | **60/60 PASS** |

---

## pytest Integration Tests (33 tests)

| Test | Result |
|------|--------|
| `test_product_jwt_protection` | PASS |
| `test_create_product_minimal` | PASS |
| `test_create_product_full` | PASS |
| `test_create_product_with_inline_variants` | PASS |
| `test_create_product_duplicate_sku_returns_409` | PASS |
| `test_create_product_invalid_price` | PASS |
| `test_list_products_pagination` | PASS |
| `test_list_products_limit` | PASS |
| `test_list_products_search` | PASS |
| `test_list_products_search_no_match` | PASS |
| `test_list_products_category_filter` | PASS |
| `test_list_products_excludes_inactive_by_default` | PASS |
| `test_list_products_is_active_false_shows_deleted` | PASS |
| `test_get_product_with_variants` | PASS |
| `test_get_product_not_found` | PASS |
| `test_update_product` | PASS |
| `test_update_deleted_product_returns_404` | PASS |
| `test_delete_product_soft` | PASS |
| `test_delete_nonexistent_product` | PASS |
| `test_add_variant` | PASS |
| `test_add_variant_to_deleted_product_returns_404` | PASS |
| `test_update_variant` | PASS |
| `test_delete_variant` | PASS |
| `test_update_variant_not_found` | PASS |
| `test_get_categories` | PASS |
| `test_categories_empty_for_new_merchant` | PASS |
| `test_merchant_isolation_get` | PASS |
| `test_merchant_isolation_patch` | PASS |
| `test_merchant_isolation_delete` | PASS |
| `test_merchant_isolation_add_variant` | PASS |
| `test_merchant_list_isolation` | PASS |
| `test_db_persistence_full_cycle` | PASS |
| `test_inventory_stock_persists_on_variant` | PASS |
| **Total** | **33/33 PASS** |

---

## Behavior Verified

| Behavior | Verified |
|----------|----------|
| Product soft-delete sets `is_active=False` (not hard-delete) | ✓ |
| Soft-deleted products hidden from list by default | ✓ |
| Soft-deleted products visible with `?is_active=false` | ✓ |
| Variant delete is hard-delete (physically removed from DB) | ✓ |
| SKU uniqueness enforced at service level AND DB level (IntegrityError) | ✓ |
| Variants created inline with product via `CreateProductRequest.variants` | ✓ |
| `GET /products/{id}` eager-loads variants via `selectinload` | ✓ |
| Category list sorted alphabetically | ✓ |
| `name_bangla`, `description_bangla` stored and retrieved correctly | ✓ |
| `low_stock_alert` default is 5; configurable per variant | ✓ |
| `total_sold` starts at 0 | ✓ |
| Pagination meta: `page`, `limit`, `total`, `total_pages` | ✓ |
| Search is case-insensitive (`ILIKE` on name, name_bangla, sku) | ✓ |
| `image_urls` defaults to empty list on product creation | ✓ |

---

## PASS/FAIL Summary

| Category | Score |
|----------|-------|
| Bugs found | 4 |
| Bugs fixed | 4 (all) |
| Live QA checks | **60/60 PASS** |
| pytest tests | **33/33 PASS** |
| Security checks | **15/15 PASS** |
| Endpoints tested | **9/9** |
| Regression impact | None |
