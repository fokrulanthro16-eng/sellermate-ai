# Orders Module QA Report

**Date:** 2026-06-22  
**Module:** Orders (`/api/v1/orders`)  
**Status:** PASS — 70/70 tests green, 7 bugs found and fixed

---

## Summary

Full audit of all 8 order endpoints. 5 production bugs identified through code review before testing (not after), all fixed. 70 integration tests written and passing. Live QA script `qa_orders.py` delivered.

---

## Endpoints Covered

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/orders` | List orders (paginated + filtered) |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/orders/export` | CSV export |
| GET | `/api/v1/orders/{id}` | Get order with items + history |
| PATCH | `/api/v1/orders/{id}` | Update delivery info |
| POST | `/api/v1/orders/{id}/status` | Change status |
| POST | `/api/v1/orders/{id}/payment` | Record payment |
| DELETE | `/api/v1/orders/{id}` | Cancel order |

---

## Bugs Found and Fixed

### BUG-ORD-001 — CRITICAL: Inventory not restored on cancel
**File:** `app/services/order_service.py`, `app/services/inventory_service.py`  
**Symptom:** Cancelling an order left product stock permanently deducted.  
**Fix:** Added `restore_for_cancelled_order()` to `inventory_service.py` and called it from `cancel_order()`. Logs `RETURN` type `InventoryLog` with `reference_type=ORDER_CANCEL`.

### BUG-ORD-002 — MEDIUM: Customer aggregate stats not rolled back on cancel
**File:** `app/services/order_service.py`  
**Symptom:** Cancelled orders still counted in `customer.total_orders` and `customer.total_spent`.  
**Fix:** Added customer stat rollback in `cancel_order()`: decrements `total_orders` (floor 0) and subtracts order total from `total_spent` (floor 0).

### BUG-ORD-003 — MEDIUM: Terminal state guard missing in change_status
**File:** `app/services/order_service.py`  
**Symptom:** Status could be changed from CANCELLED or RETURNED orders.  
**Fix:** Added `_TERMINAL_STATUSES = {OrderStatus.CANCELLED, OrderStatus.RETURNED}` guard at top of `change_status()`.

### BUG-ORD-004 — MEDIUM: Payment allowed on cancelled orders
**File:** `app/services/order_service.py`  
**Symptom:** `record_payment` processed payments against cancelled orders.  
**Fix:** Added early `if order.status == OrderStatus.CANCELLED: raise BadRequestException(...)` check in `record_payment()`.

### BUG-ORD-005 — LOW: Float arithmetic in financial calculations
**File:** `app/services/order_service.py`  
**Symptom:** `subtotal`, `total_amount`, `customer.total_spent` used Python `float` arithmetic causing potential precision errors on monetary values.  
**Fix:** Changed all financial math to `Decimal` throughout `create_order()`, `record_payment()`, and `cancel_order()`.

### BUG-ORD-006 — MEDIUM: MissingGreenlet on cancel_order serialisation
**File:** `app/services/order_service.py`  
**Symptom:** `DELETE /orders/{id}` returned HTTP 500. Root cause: after `cancel_order` does async DB calls for inventory restore and customer update, SQLAlchemy autoflush sets `updated_at` server-side and expires it. Pydantic's synchronous `model_validate` then can't lazy-load it.  
**Fix:** Added `await db.refresh(order)` before returning in `cancel_order()`.

### BUG-ORD-007 — LOW: CSV export limit validation error
**File:** `app/routers/orders.py`  
**Symptom:** `GET /orders/export` returned HTTP 422 because the router passed `limit=5000` to `OrderFilters` which enforces `le=100`.  
**Fix:** Removed the `limit=5000` from router's `OrderFilters` construction. The `export_csv` service already overrides the limit via attribute assignment (bypassing Pydantic validation).

---

## Test Suite Results

```
tests/test_orders.py — 70 passed in 315s
```

| Class | Tests | Result |
|-------|-------|--------|
| TestJWTProtection | 8 | PASS |
| TestCreateOrder | 14 | PASS |
| TestGetOrder | 4 | PASS |
| TestUpdateOrder | 2 | PASS |
| TestChangeStatus | 6 | PASS |
| TestRecordPayment | 7 | PASS |
| TestCancelOrder | 7 | PASS |
| TestListOrders | 7 | PASS |
| TestCSVExport | 4 | PASS |
| TestMerchantIsolation | 6 | PASS |
| TestDBPersistence | 4 | PASS |
| **TOTAL** | **70** | **PASS** |

---

## Coverage Details

### JWT Protection
- All 8 endpoints return 401 without `Authorization` header ✓

### Order Creation
- Returns 201 with correct schema ✓
- Default status = PENDING, payment_status = UNPAID, paid_amount = 0 ✓
- Subtotal = sum(variant.price × qty) ✓
- Discount applied, shipping applied, total_amount correct ✓
- Invalid customer → 404 ✓
- Invalid product → 404 ✓
- Insufficient stock → 400 ✓
- Empty items array → 422 ✓
- `order_number` generated (format `SM-YYYYMMDD-NNNN`) ✓
- Inventory deducted from variant stock on create ✓
- Customer `total_orders` and `total_spent` incremented ✓

### Status Lifecycle
- PENDING → CONFIRMED → DELIVERED transitions ✓
- `delivered_at` timestamp set when DELIVERED ✓
- Status note saved in `status_history` ✓
- Cannot change status from CANCELLED → 400 ✓
- Cannot change status from RETURNED → 400 ✓
- Unknown order → 404 ✓

### Payment Recording
- Partial payment sets `payment_status=PARTIAL` ✓
- Full payment sets `payment_status=PAID` ✓
- Overpayment → 400 ✓
- Payment on CANCELLED order → 400 ✓
- Zero amount → 422 ✓
- Cumulative payments sum correctly ✓

### Order Cancellation
- Cancel PENDING/CONFIRMED → 200, status=CANCELLED ✓
- Inventory restored to pre-order level (Bug 1 fix) ✓
- Customer stats rolled back (Bug 2 fix) ✓
- Status history entry added ✓
- Cannot cancel SHIPPED → 400 ✓
- Cannot cancel already CANCELLED → 400 ✓

### Filtering & Pagination
- Status filter returns only matching orders ✓
- Payment status filter works ✓
- Search by order number works ✓
- Pagination limit enforced ✓
- Pagination meta (total, pages) accurate ✓

### CSV Export
- Returns 200 with `text/csv` Content-Type ✓
- Response has `Content-Disposition` attachment header ✓
- CSV contains header row with expected columns ✓
- CSV contains order data ✓
- Requires auth (401 without token) ✓

### Merchant Isolation
- List returns only own merchant's orders ✓
- GET another merchant's order → 404 ✓
- PATCH another merchant's order → 404 ✓
- Change status on another merchant's order → 404 ✓
- Cancel another merchant's order → 404 ✓
- Create order with another merchant's customer → 404 ✓

---

## Files Modified

| File | Change |
|------|--------|
| `app/services/inventory_service.py` | Added `restore_for_cancelled_order()` |
| `app/services/order_service.py` | Decimal arithmetic, terminal state guard, cancel payment guard, inventory restore call, customer stat rollback, `db.refresh(order)` |
| `app/routers/orders.py` | Removed `limit=5000` from export endpoint |
| `tests/test_orders.py` | New — 70-test integration suite |
| `qa_orders.py` | New — live server QA script |
| `tests/conftest.py` | Removed destructive `drop_all` from teardown |

---

## Live QA Script

`qa_orders.py` — run against a live server:
```
uvicorn app.main:app --reload
python qa_orders.py
```

Covers 17 test groups (T01–T17): JWT, create, inventory deduction, get details, update, status transitions, terminal state guard, payment, cancelled payment guard, cancel + inventory restore, customer stats rollback, cancel restrictions, list + filters, CSV export, merchant isolation, validation errors, DB persistence.
