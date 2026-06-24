"""
Analytics module integration tests.
Covers: all 7 endpoints, dashboard metrics, revenue series, order breakdown,
top products, top customers, customer metrics, inventory health, merchant isolation.
"""

import uuid
import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────

def _uid8() -> str:
    return f"{uuid.uuid4().int % 100_000_000:08d}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(client: AsyncClient, label: str) -> tuple[str, str]:
    digits = _uid8()
    phone = f"+88017{digits}"
    r = await client.post("/api/v1/auth/register", json={
        "email": f"anl{label}{digits}@test.com",
        "phone": phone,
        "password": "TestPass1!",
        "business_name": f"Analytic Biz {label}",
        "owner_name": f"Owner {label}",
        "business_type": "FASHION_CLOTHING",
    })
    assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"
    r2 = await client.post("/api/v1/auth/login", json={"identifier": phone, "password": "TestPass1!"})
    assert r2.status_code == 200, r2.text
    d = r2.json()["data"]
    return d["tokens"]["access_token"], d["merchant"]["id"]


async def create_product_and_variant(client: AsyncClient, token: str, price: str = "100.00") -> tuple[str, str]:
    r = await client.post("/api/v1/products", json={
        "name": f"Prod {_uid8()}",
        "category": "CLOTHING",
        "base_price": price,
        "variants": [{"name": "Default", "sku": f"SKU-{_uid8()}", "price": price,
                       "stock_quantity": 200, "low_stock_alert": 5}],
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    pid = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/products/{pid}", headers=auth_headers(token))
    vid = r2.json()["data"]["variants"][0]["id"]
    return pid, vid


async def create_customer(client: AsyncClient, token: str) -> str:
    r = await client.post("/api/v1/customers", json={
        "name": f"Cust {_uid8()}", "phone": f"+88018{_uid8()}",
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


async def create_order(client: AsyncClient, token: str, cid: str, pid: str, vid: str,
                       qty: int = 1, status: str | None = None) -> dict:
    r = await client.post("/api/v1/orders", json={
        "customer_id": cid,
        "items": [{"product_id": pid, "variant_id": vid, "quantity": qty}],
        "payment_method": "COD",
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    order = r.json()["data"]
    if status and status != "PENDING":
        r2 = await client.post(f"/api/v1/orders/{order['id']}/status",
                                json={"status": status}, headers=auth_headers(token))
        assert r2.status_code == 200, r2.text
        order = r2.json()["data"]
    return order


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
async def merchant_a(client: AsyncClient):
    return await register_and_login(client, "anlA")


@pytest.fixture
async def merchant_b(client: AsyncClient):
    return await register_and_login(client, "anlB")


@pytest.fixture
async def setup_a(client: AsyncClient, merchant_a: tuple):
    """Returns (token, pid, vid, cid) with a few orders created."""
    token, _ = merchant_a
    pid, vid = await create_product_and_variant(client, token, price="500.00")
    cid1 = await create_customer(client, token)
    cid2 = await create_customer(client, token)
    # 2 delivered orders for cid1 (repeat customer)
    await create_order(client, token, cid1, pid, vid, qty=2, status="DELIVERED")
    await create_order(client, token, cid1, pid, vid, qty=1, status="DELIVERED")
    # 1 cancelled order
    o_cancel = await create_order(client, token, cid1, pid, vid, qty=1)
    await client.delete(f"/api/v1/orders/{o_cancel['id']}", headers=auth_headers(token))
    # 1 pending order for cid2
    await create_order(client, token, cid2, pid, vid, qty=1)
    return token, pid, vid, cid1


DATE_RANGE = {"from_date": "2000-01-01", "to_date": "2099-12-31"}
# Overview calculates prior period = from_date - (to_date - from_date). Use a modest range
# so prior_from stays above 1970 (Windows timestamptz minimum).
OVERVIEW_RANGE = {"from_date": "2024-01-01", "to_date": "2026-12-31"}


# ── JWT Protection ────────────────────────────────────────────────

class TestJWTProtection:
    ENDPOINTS = [
        ("GET",  "/api/v1/analytics/dashboard"),
        ("GET",  "/api/v1/analytics/customers"),
        ("GET",  "/api/v1/analytics/overview"),
        ("GET",  "/api/v1/analytics/revenue"),
        ("GET",  "/api/v1/analytics/orders"),
        ("GET",  "/api/v1/analytics/products/top"),
        ("GET",  "/api/v1/analytics/inventory"),
    ]

    async def test_all_endpoints_require_auth(self, client: AsyncClient):
        for method, path in self.ENDPOINTS:
            resp = await client.request(method, path)
            assert resp.status_code == 401, f"{path} returned {resp.status_code}"


# ── Dashboard ─────────────────────────────────────────────────────

class TestDashboard:
    async def test_dashboard_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_dashboard_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        for field in ["today_revenue", "weekly_revenue", "monthly_revenue",
                      "total_orders", "delivered_orders", "cancelled_orders",
                      "repeat_customers", "average_order_value",
                      "top_products", "top_customers"]:
            assert field in data, f"Missing field: {field}"

    async def test_dashboard_delivered_orders_count(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        assert data["delivered_orders"] >= 2

    async def test_dashboard_cancelled_orders_count(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        assert data["cancelled_orders"] >= 1

    async def test_dashboard_repeat_customers(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        # cid1 has 2+ delivered orders → repeat customer
        assert data["repeat_customers"] >= 1

    async def test_dashboard_top_products_list(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        assert isinstance(data["top_products"], list)

    async def test_dashboard_top_customers_list(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        assert isinstance(data["top_customers"], list)
        if data["top_customers"]:
            tc = data["top_customers"][0]
            for f in ["customer_id", "customer_name", "total_orders", "total_spent"]:
                assert f in tc, f"Missing top_customer field: {f}"

    async def test_dashboard_revenue_non_negative(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token))
        data = r.json()["data"]
        assert data["monthly_revenue"] >= 0
        assert data["weekly_revenue"] >= 0
        assert data["today_revenue"] >= 0


# ── Customer Metrics ──────────────────────────────────────────────

class TestCustomerMetrics:
    async def test_customers_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/customers",
                              params=DATE_RANGE, headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_customers_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/customers",
                              params=DATE_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        assert "new_customers" in data
        assert "returning_customers" in data
        assert "top_customers" in data
        assert isinstance(data["top_customers"], list)

    async def test_new_customers_positive(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/customers",
                              params=DATE_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        assert data["new_customers"] >= 2

    async def test_returning_customers_positive(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/customers",
                              params=DATE_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        assert data["returning_customers"] >= 1

    async def test_missing_dates_returns_422(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get("/api/v1/analytics/customers", headers=auth_headers(token))
        assert r.status_code == 422


# ── Overview ──────────────────────────────────────────────────────

class TestOverview:
    async def test_overview_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/overview",
                              params=OVERVIEW_RANGE, headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_overview_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/overview",
                              params=OVERVIEW_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        for f in ["total_revenue", "total_orders", "total_customers",
                   "average_order_value", "revenue_change_pct",
                   "orders_change_pct", "customers_change_pct"]:
            assert f in data, f"Missing field: {f}"

    async def test_overview_total_revenue_positive(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/overview",
                              params=OVERVIEW_RANGE, headers=auth_headers(token))
        assert r.json()["data"]["total_revenue"] >= 0

    async def test_overview_missing_dates_422(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get("/api/v1/analytics/overview", headers=auth_headers(token))
        assert r.status_code == 422


# ── Revenue Series ────────────────────────────────────────────────

class TestRevenueSeries:
    async def test_revenue_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/revenue",
                              params={**DATE_RANGE, "period": "day"}, headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_revenue_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/revenue",
                              params={**DATE_RANGE, "period": "day"}, headers=auth_headers(token))
        data = r.json()["data"]
        assert "period" in data
        assert "points" in data
        assert isinstance(data["points"], list)
        if data["points"]:
            pt = data["points"][0]
            assert "date" in pt and "revenue" in pt and "orders" in pt

    async def test_revenue_period_week(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/revenue",
                              params={**DATE_RANGE, "period": "week"}, headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["period"] == "week"

    async def test_revenue_invalid_period_422(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/revenue",
                              params={**DATE_RANGE, "period": "year"}, headers=auth_headers(token))
        assert r.status_code == 422


# ── Order Breakdown ───────────────────────────────────────────────

class TestOrderBreakdown:
    async def test_breakdown_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/orders",
                              params=DATE_RANGE, headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_breakdown_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/orders",
                              params=DATE_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        assert "by_status" in data
        assert "by_channel" in data
        assert "by_payment_method" in data
        assert "by_payment_status" in data

    async def test_breakdown_has_delivered_in_status(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/orders",
                              params=DATE_RANGE, headers=auth_headers(token))
        data = r.json()["data"]
        assert "DELIVERED" in data["by_status"]

    async def test_breakdown_channel_list(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/orders",
                              params=DATE_RANGE, headers=auth_headers(token))
        channels = r.json()["data"]["by_channel"]
        assert isinstance(channels, list)
        if channels:
            ch = channels[0]
            assert "channel" in ch and "count" in ch and "revenue" in ch


# ── Top Products ──────────────────────────────────────────────────

class TestTopProducts:
    async def test_top_products_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/products/top",
                              params=DATE_RANGE, headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_top_products_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/products/top",
                              params=DATE_RANGE, headers=auth_headers(token))
        products = r.json()["data"]
        assert isinstance(products, list)
        if products:
            p = products[0]
            for f in ["product_id", "product_name", "total_revenue", "total_quantity"]:
                assert f in p, f"Missing field: {f}"

    async def test_top_products_has_data(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/products/top",
                              params=DATE_RANGE, headers=auth_headers(token))
        assert len(r.json()["data"]) >= 1

    async def test_top_products_limit(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/products/top",
                              params={**DATE_RANGE, "limit": 1}, headers=auth_headers(token))
        assert len(r.json()["data"]) <= 1


# ── Inventory Health ──────────────────────────────────────────────

class TestInventoryHealth:
    async def test_inventory_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/inventory", headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_inventory_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/inventory", headers=auth_headers(token))
        data = r.json()["data"]
        for f in ["total_variants", "in_stock", "low_stock", "out_of_stock", "low_stock_items"]:
            assert f in data, f"Missing field: {f}"

    async def test_inventory_counts_non_negative(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.get("/api/v1/analytics/inventory", headers=auth_headers(token))
        data = r.json()["data"]
        assert data["total_variants"] >= 0
        assert data["in_stock"] >= 0
        assert data["low_stock"] >= 0
        assert data["out_of_stock"] >= 0


# ── Merchant Isolation ────────────────────────────────────────────

class TestMerchantIsolation:
    async def test_dashboard_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        _, pid, vid, cid = setup_a
        token_b, _ = merchant_b
        # Merchant B has no data — dashboard should return zeros
        r = await client.get("/api/v1/analytics/dashboard", headers=auth_headers(token_b))
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["delivered_orders"] == 0
        assert data["monthly_revenue"] == 0.0

    async def test_overview_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        token_b, _ = merchant_b
        r = await client.get("/api/v1/analytics/overview",
                              params=OVERVIEW_RANGE, headers=auth_headers(token_b))
        assert r.status_code == 200
        assert r.json()["data"]["total_orders"] == 0

    async def test_top_products_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        token_b, _ = merchant_b
        r = await client.get("/api/v1/analytics/products/top",
                              params=DATE_RANGE, headers=auth_headers(token_b))
        assert r.status_code == 200
        assert r.json()["data"] == []
