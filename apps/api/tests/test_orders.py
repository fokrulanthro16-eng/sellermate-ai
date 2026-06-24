"""
Orders module integration tests.
Covers: all 8 endpoints, calculations, inventory deduction/rollback,
customer stats, merchant isolation, status transitions, payment tracking.
"""

import uuid
import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────

def _uid8() -> str:
    return f"{uuid.uuid4().int % 100_000_000:08d}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(client: AsyncClient, label: str) -> tuple[str, str]:
    digits = _uid8()
    phone = f"+88015{digits}"
    r = await client.post("/api/v1/auth/register", json={
        "email": f"ord{label}{digits}@test.com",
        "phone": phone,
        "password": "TestPass1!",
        "business_name": f"Order Biz {label}",
        "owner_name": f"Owner {label}",
        "business_type": "FASHION_CLOTHING",
    })
    assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"

    r = await client.post("/api/v1/auth/login", json={"identifier": phone, "password": "TestPass1!"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    return d["tokens"]["access_token"], d["merchant"]["id"]


async def create_product_with_variant(
    client: AsyncClient,
    token: str,
    *,
    stock: int = 50,
    price: str = "200.00",
    low_stock_alert: int = 5,
) -> tuple[str, str]:
    """Returns (product_id, variant_id)."""
    r = await client.post("/api/v1/products", json={
        "name": f"Test Product {_uid8()}",
        "category": "CLOTHING",
        "base_price": price,
        "variants": [{
            "name": "Default",
            "sku": f"SKU-{_uid8()}",
            "price": price,
            "stock_quantity": stock,
            "low_stock_alert": low_stock_alert,
        }],
    }, headers=auth_headers(token))
    assert r.status_code == 201, f"create product failed: {r.status_code} {r.text}"
    pid = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/products/{pid}", headers=auth_headers(token))
    vid = r2.json()["data"]["variants"][0]["id"]
    return pid, vid


async def create_customer(client: AsyncClient, token: str) -> str:
    """Returns customer_id."""
    r = await client.post("/api/v1/customers", json={
        "name": f"Test Customer {_uid8()}",
        "phone": f"+88016{_uid8()}",
    }, headers=auth_headers(token))
    assert r.status_code == 201, f"create customer failed: {r.status_code} {r.text}"
    return r.json()["data"]["id"]


async def create_order(
    client: AsyncClient,
    token: str,
    customer_id: str,
    product_id: str,
    variant_id: str,
    *,
    quantity: int = 1,
    discount: str = "0",
    shipping: str = "0",
) -> dict:
    r = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "variant_id": variant_id, "quantity": quantity}],
        "discount_amount": discount,
        "shipping_cost": shipping,
        "payment_method": "COD",
    }, headers=auth_headers(token))
    assert r.status_code == 201, f"create order failed: {r.status_code} {r.text}"
    return r.json()["data"]


async def get_stock(client: AsyncClient, token: str, variant_id: str) -> int:
    r = await client.get(f"/api/v1/inventory?variant_id={variant_id}", headers=auth_headers(token))
    items = r.json()["data"]
    for item in items:
        if item["variant_id"] == variant_id:
            return item["stock_quantity"]
    return -1


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
async def merchant_a(client: AsyncClient):
    return await register_and_login(client, "ordA")


@pytest.fixture
async def merchant_b(client: AsyncClient):
    return await register_and_login(client, "ordB")


@pytest.fixture
async def setup_a(client: AsyncClient, merchant_a: tuple):
    """Returns (token, product_id, variant_id, customer_id)."""
    token, _ = merchant_a
    pid, vid = await create_product_with_variant(client, token, stock=50)
    cid = await create_customer(client, token)
    return token, pid, vid, cid


@pytest.fixture
async def order_a(client: AsyncClient, setup_a: tuple):
    """Creates a fresh PENDING order; returns (token, order_dict, variant_id)."""
    token, pid, vid, cid = setup_a
    order = await create_order(client, token, cid, pid, vid, quantity=2)
    return token, order, vid


# ── JWT Protection ────────────────────────────────────────────────

class TestJWTProtection:
    FAKE = "00000000-0000-0000-0000-000000000000"

    async def test_list_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/orders")).status_code == 401

    async def test_create_requires_auth(self, client: AsyncClient):
        assert (await client.post("/api/v1/orders", json={})).status_code == 401

    async def test_export_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/orders/export")).status_code == 401

    async def test_get_requires_auth(self, client: AsyncClient):
        assert (await client.get(f"/api/v1/orders/{self.FAKE}")).status_code == 401

    async def test_patch_requires_auth(self, client: AsyncClient):
        assert (await client.patch(f"/api/v1/orders/{self.FAKE}", json={})).status_code == 401

    async def test_status_requires_auth(self, client: AsyncClient):
        assert (await client.post(f"/api/v1/orders/{self.FAKE}/status", json={"status": "CONFIRMED"})).status_code == 401

    async def test_payment_requires_auth(self, client: AsyncClient):
        assert (await client.post(f"/api/v1/orders/{self.FAKE}/payment", json={"amount": "100", "method": "COD"})).status_code == 401

    async def test_cancel_requires_auth(self, client: AsyncClient):
        assert (await client.delete(f"/api/v1/orders/{self.FAKE}")).status_code == 401


# ── Create Order ──────────────────────────────────────────────────

class TestCreateOrder:
    async def test_create_returns_201(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        r = await client.post("/api/v1/orders", json={
            "customer_id": cid,
            "items": [{"product_id": pid, "variant_id": vid, "quantity": 1}],
        }, headers=auth_headers(token))
        assert r.status_code == 201

    async def test_response_schema(self, client: AsyncClient, order_a: tuple):
        _, order, _ = order_a
        for field in ["id", "merchant_id", "customer_id", "order_number", "status",
                      "channel", "subtotal", "discount_amount", "shipping_cost",
                      "total_amount", "paid_amount", "due_amount", "payment_method",
                      "payment_status", "created_at", "updated_at"]:
            assert field in order, f"Missing field: {field}"

    async def test_status_defaults_to_pending(self, client: AsyncClient, order_a: tuple):
        _, order, _ = order_a
        assert order["status"] == "PENDING"

    async def test_payment_status_defaults_to_unpaid(self, client: AsyncClient, order_a: tuple):
        _, order, _ = order_a
        assert order["payment_status"] == "UNPAID"

    async def test_paid_amount_defaults_to_zero(self, client: AsyncClient, order_a: tuple):
        _, order, _ = order_a
        assert float(order["paid_amount"]) == 0.0

    async def test_subtotal_calculation(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        order = await create_order(client, token, cid, pid, vid, quantity=3)
        # price=200.00 * qty=3 = 600.00, discount=0, shipping=0 → total=600
        assert float(order["subtotal"]) == 600.0
        assert float(order["total_amount"]) == 600.0
        assert float(order["due_amount"]) == 600.0

    async def test_discount_applied(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        order = await create_order(client, token, cid, pid, vid, quantity=2, discount="50")
        # 200*2=400 - 50 = 350
        assert float(order["total_amount"]) == 350.0
        assert float(order["due_amount"]) == 350.0

    async def test_shipping_applied(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        order = await create_order(client, token, cid, pid, vid, quantity=1, shipping="60")
        # 200 + 60 = 260
        assert float(order["total_amount"]) == 260.0

    async def test_invalid_customer_returns_404(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, _ = setup_a
        r = await client.post("/api/v1/orders", json={
            "customer_id": str(uuid.uuid4()),
            "items": [{"product_id": pid, "variant_id": vid, "quantity": 1}],
        }, headers=auth_headers(token))
        assert r.status_code == 404

    async def test_invalid_product_returns_404(self, client: AsyncClient, setup_a: tuple):
        token, _, _, cid = setup_a
        r = await client.post("/api/v1/orders", json={
            "customer_id": cid,
            "items": [{"product_id": str(uuid.uuid4()), "quantity": 1}],
        }, headers=auth_headers(token))
        assert r.status_code == 404

    async def test_insufficient_stock_returns_400(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        r = await client.post("/api/v1/orders", json={
            "customer_id": cid,
            "items": [{"product_id": pid, "variant_id": vid, "quantity": 9999}],
        }, headers=auth_headers(token))
        assert r.status_code == 400

    async def test_empty_items_returns_422(self, client: AsyncClient, setup_a: tuple):
        token, _, _, cid = setup_a
        r = await client.post("/api/v1/orders", json={
            "customer_id": cid,
            "items": [],
        }, headers=auth_headers(token))
        assert r.status_code == 422

    async def test_order_number_generated(self, client: AsyncClient, order_a: tuple):
        _, order, _ = order_a
        assert order["order_number"].startswith("SM-")

    async def test_inventory_deducted_on_create(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        stock_before = await get_stock(client, token, vid)
        await create_order(client, token, cid, pid, vid, quantity=3)
        stock_after = await get_stock(client, token, vid)
        assert stock_after == stock_before - 3

    async def test_customer_stats_updated_on_create(self, client: AsyncClient, setup_a: tuple):
        token, pid, vid, cid = setup_a
        r_before = await client.get(f"/api/v1/customers/{cid}", headers=auth_headers(token))
        orders_before = r_before.json()["data"]["total_orders"]

        await create_order(client, token, cid, pid, vid, quantity=1)

        r_after = await client.get(f"/api/v1/customers/{cid}", headers=auth_headers(token))
        assert r_after.json()["data"]["total_orders"] == orders_before + 1


# ── Get Order ─────────────────────────────────────────────────────

class TestGetOrder:
    async def test_get_order_returns_200(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.status_code == 200

    async def test_get_order_has_items(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        d = r.json()["data"]
        assert "items" in d
        assert len(d["items"]) == 1
        assert d["items"][0]["quantity"] == 2

    async def test_get_order_has_status_history(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        d = r.json()["data"]
        assert "status_history" in d
        assert len(d["status_history"]) >= 1
        assert d["status_history"][0]["status"] == "PENDING"

    async def test_get_unknown_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get(f"/api/v1/orders/{uuid.uuid4()}", headers=auth_headers(token))
        assert r.status_code == 404


# ── Update Order ──────────────────────────────────────────────────

class TestUpdateOrder:
    async def test_update_delivery_info(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.patch(f"/api/v1/orders/{order['id']}", json={
            "delivery_address": "123 Main St",
            "courier_name": "Pathao",
            "tracking_number": "PTH-123",
        }, headers=auth_headers(token))
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["courier_name"] == "Pathao"
        assert d["tracking_number"] == "PTH-123"

    async def test_update_unknown_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.patch(f"/api/v1/orders/{uuid.uuid4()}", json={}, headers=auth_headers(token))
        assert r.status_code == 404


# ── Change Status ─────────────────────────────────────────────────

class TestChangeStatus:
    async def test_change_to_confirmed(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.post(f"/api/v1/orders/{order['id']}/status",
                               json={"status": "CONFIRMED"}, headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "CONFIRMED"

    async def test_change_to_delivered_sets_timestamp(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/status",
                          json={"status": "DELIVERED"}, headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.json()["data"]["delivered_at"] is not None

    async def test_status_history_appended(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/status",
                          json={"status": "CONFIRMED", "note": "Verified"}, headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        history = r.json()["data"]["status_history"]
        assert len(history) >= 2
        confirmed_entry = next(h for h in history if h["status"] == "CONFIRMED")
        assert confirmed_entry["note"] == "Verified"

    async def test_cannot_change_from_cancelled(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        # Cancel first
        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        # Then try to change status
        r = await client.post(f"/api/v1/orders/{order['id']}/status",
                               json={"status": "CONFIRMED"}, headers=auth_headers(token))
        assert r.status_code == 400

    async def test_cannot_change_from_returned(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/status",
                          json={"status": "RETURNED"}, headers=auth_headers(token))
        r = await client.post(f"/api/v1/orders/{order['id']}/status",
                               json={"status": "DELIVERED"}, headers=auth_headers(token))
        assert r.status_code == 400

    async def test_unknown_order_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(f"/api/v1/orders/{uuid.uuid4()}/status",
                               json={"status": "CONFIRMED"}, headers=auth_headers(token))
        assert r.status_code == 404


# ── Record Payment ────────────────────────────────────────────────

class TestRecordPayment:
    async def test_partial_payment(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        total = float(order["total_amount"])
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": "100", "method": "BKASH"},
                               headers=auth_headers(token))
        assert r.status_code == 200
        d = r.json()["data"]
        assert float(d["paid_amount"]) == 100.0
        assert float(d["due_amount"]) == total - 100
        assert d["payment_status"] == "PARTIAL"

    async def test_full_payment_marks_paid(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        total = order["total_amount"]
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": str(total), "method": "BKASH"},
                               headers=auth_headers(token))
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["payment_status"] == "PAID"
        assert float(d["due_amount"]) == 0.0

    async def test_overpayment_returns_400(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        total = float(order["total_amount"])
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": str(total + 1), "method": "COD"},
                               headers=auth_headers(token))
        assert r.status_code == 400

    async def test_payment_on_cancelled_returns_400(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": "100", "method": "COD"},
                               headers=auth_headers(token))
        assert r.status_code == 400

    async def test_zero_amount_returns_422(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": "0", "method": "COD"},
                               headers=auth_headers(token))
        assert r.status_code == 422

    async def test_cumulative_payments(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        total = float(order["total_amount"])
        await client.post(f"/api/v1/orders/{order['id']}/payment",
                          json={"amount": str(total / 2), "method": "COD"},
                          headers=auth_headers(token))
        r = await client.post(f"/api/v1/orders/{order['id']}/payment",
                               json={"amount": str(total / 2), "method": "COD"},
                               headers=auth_headers(token))
        assert r.json()["data"]["payment_status"] == "PAID"

    async def test_unknown_order_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(f"/api/v1/orders/{uuid.uuid4()}/payment",
                               json={"amount": "100", "method": "COD"},
                               headers=auth_headers(token))
        assert r.status_code == 404


# ── Cancel Order ──────────────────────────────────────────────────

class TestCancelOrder:
    async def test_cancel_returns_200(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "CANCELLED"

    async def test_cancel_restores_inventory(self, client: AsyncClient, setup_a: tuple):
        """Bug 1 fix: inventory must be restored after cancellation."""
        token, pid, vid, cid = setup_a
        stock_before = await get_stock(client, token, vid)

        order = await create_order(client, token, cid, pid, vid, quantity=5)
        stock_after_create = await get_stock(client, token, vid)
        assert stock_after_create == stock_before - 5

        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        stock_after_cancel = await get_stock(client, token, vid)
        assert stock_after_cancel == stock_before

    async def test_cancel_rollbacks_customer_stats(self, client: AsyncClient, setup_a: tuple):
        """Bug 2 fix: customer stats must be decremented on cancellation."""
        token, pid, vid, cid = setup_a
        r_before = await client.get(f"/api/v1/customers/{cid}", headers=auth_headers(token))
        orders_before = r_before.json()["data"]["total_orders"]

        order = await create_order(client, token, cid, pid, vid)
        r_mid = await client.get(f"/api/v1/customers/{cid}", headers=auth_headers(token))
        assert r_mid.json()["data"]["total_orders"] == orders_before + 1

        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        r_after = await client.get(f"/api/v1/customers/{cid}", headers=auth_headers(token))
        assert r_after.json()["data"]["total_orders"] == orders_before

    async def test_cancel_adds_status_history(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        history = r.json()["data"]["status_history"]
        assert any(h["status"] == "CANCELLED" for h in history)

    async def test_cannot_cancel_shipped_order(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/status",
                          json={"status": "SHIPPED"}, headers=auth_headers(token))
        r = await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.status_code == 400

    async def test_cannot_cancel_already_cancelled(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        r = await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.status_code == 400

    async def test_unknown_order_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.delete(f"/api/v1/orders/{uuid.uuid4()}", headers=auth_headers(token))
        assert r.status_code == 404


# ── List Orders ───────────────────────────────────────────────────

class TestListOrders:
    async def test_list_returns_200(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders", headers=auth_headers(token))
        assert r.status_code == 200

    async def test_list_has_pagination_meta(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders", headers=auth_headers(token))
        meta = r.json().get("meta", {})
        for key in ["page", "limit", "total", "total_pages"]:
            assert key in meta

    async def test_list_contains_created_order(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get("/api/v1/orders", headers=auth_headers(token))
        ids = [o["id"] for o in r.json()["data"]]
        assert order["id"] in ids

    async def test_status_filter(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders?status=PENDING", headers=auth_headers(token))
        assert r.status_code == 200
        results = r.json()["data"]
        assert all(o["status"] == "PENDING" for o in results)

    async def test_payment_status_filter(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders?payment_status=UNPAID", headers=auth_headers(token))
        assert r.status_code == 200
        results = r.json()["data"]
        assert all(o["payment_status"] == "UNPAID" for o in results)

    async def test_search_by_order_number(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        order_num = order["order_number"]
        r = await client.get(f"/api/v1/orders?search={order_num}", headers=auth_headers(token))
        assert r.status_code == 200
        assert any(o["order_number"] == order_num for o in r.json()["data"])

    async def test_pagination_limit(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders?limit=1", headers=auth_headers(token))
        assert r.status_code == 200
        assert len(r.json()["data"]) <= 1
        assert r.json()["meta"]["limit"] == 1


# ── CSV Export ────────────────────────────────────────────────────

class TestCSVExport:
    async def test_export_returns_200(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders/export", headers=auth_headers(token))
        assert r.status_code == 200

    async def test_export_content_type(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders/export", headers=auth_headers(token))
        assert "text/csv" in r.headers.get("content-type", "")

    async def test_export_has_header(self, client: AsyncClient, order_a: tuple):
        token, _, _ = order_a
        r = await client.get("/api/v1/orders/export", headers=auth_headers(token))
        text = r.content.decode("utf-8-sig")
        assert "order_number" in text.lower()

    async def test_export_contains_order_data(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get("/api/v1/orders/export", headers=auth_headers(token))
        text = r.content.decode("utf-8-sig")
        assert order["order_number"] in text


# ── Merchant Isolation ────────────────────────────────────────────

class TestMerchantIsolation:
    async def test_list_excludes_other_merchant_orders(
        self, client: AsyncClient, order_a: tuple, merchant_b: tuple
    ):
        token_a, order, _ = order_a
        token_b, _ = merchant_b
        r = await client.get("/api/v1/orders", headers=auth_headers(token_b))
        ids = [o["id"] for o in r.json()["data"]]
        assert order["id"] not in ids

    async def test_get_other_merchant_order_returns_404(
        self, client: AsyncClient, order_a: tuple, merchant_b: tuple
    ):
        _, order, _ = order_a
        token_b, _ = merchant_b
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_patch_other_merchant_order_returns_404(
        self, client: AsyncClient, order_a: tuple, merchant_b: tuple
    ):
        _, order, _ = order_a
        token_b, _ = merchant_b
        r = await client.patch(f"/api/v1/orders/{order['id']}", json={},
                                headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_change_status_other_merchant_returns_404(
        self, client: AsyncClient, order_a: tuple, merchant_b: tuple
    ):
        _, order, _ = order_a
        token_b, _ = merchant_b
        r = await client.post(f"/api/v1/orders/{order['id']}/status",
                               json={"status": "CONFIRMED"},
                               headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_cancel_other_merchant_order_returns_404(
        self, client: AsyncClient, order_a: tuple, merchant_b: tuple
    ):
        _, order, _ = order_a
        token_b, _ = merchant_b
        r = await client.delete(f"/api/v1/orders/{order['id']}", headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_cross_merchant_customer_order_rejected(
        self, client: AsyncClient, merchant_a: tuple, merchant_b: tuple
    ):
        """Merchant B's customer cannot be used in Merchant A's order."""
        token_a, _ = merchant_a
        token_b, _ = merchant_b
        # Create a product for merchant A
        pid, vid = await create_product_with_variant(client, token_a)
        # Create a customer for merchant B
        cid_b = await create_customer(client, token_b)
        # Merchant A tries to create order with merchant B's customer
        r = await client.post("/api/v1/orders", json={
            "customer_id": cid_b,
            "items": [{"product_id": pid, "variant_id": vid, "quantity": 1}],
        }, headers=auth_headers(token_a))
        assert r.status_code == 404


# ── DB Persistence ────────────────────────────────────────────────

class TestDBPersistence:
    async def test_order_persists(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["id"] == order["id"]

    async def test_update_persists(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.patch(f"/api/v1/orders/{order['id']}",
                           json={"tracking_number": "TRACK-XYZ"},
                           headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.json()["data"]["tracking_number"] == "TRACK-XYZ"

    async def test_status_change_persists(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/status",
                          json={"status": "CONFIRMED"}, headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert r.json()["data"]["status"] == "CONFIRMED"

    async def test_payment_persists(self, client: AsyncClient, order_a: tuple):
        token, order, _ = order_a
        await client.post(f"/api/v1/orders/{order['id']}/payment",
                          json={"amount": "50", "method": "BKASH"},
                          headers=auth_headers(token))
        r = await client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers(token))
        assert float(r.json()["data"]["paid_amount"]) == 50.0
