"""
Strategic Agent Layer integration tests.
Covers: POST /run, GET /insights, GET /trust-score, GET /fraud-report,
trust scoring logic, fraud detection logic, merchant isolation, JWT protection.
"""

import uuid
import pytest
from httpx import AsyncClient

BASE = "/api/v1/ai/strategic"


# ── Helpers ───────────────────────────────────────────────────────

def _uid8() -> str:
    return f"{uuid.uuid4().int % 100_000_000:08d}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(client: AsyncClient, label: str) -> tuple[str, str]:
    digits = _uid8()
    phone = f"+88019{digits}"
    r = await client.post("/api/v1/auth/register", json={
        "email": f"str{label}{digits}@test.com",
        "phone": phone,
        "password": "TestPass1!",
        "business_name": f"Strategic Biz {label}",
        "owner_name": f"Owner {label}",
        "business_type": "FASHION_CLOTHING",
    })
    assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"
    r2 = await client.post("/api/v1/auth/login", json={"identifier": phone, "password": "TestPass1!"})
    assert r2.status_code == 200, r2.text
    d = r2.json()["data"]
    return d["tokens"]["access_token"], d["merchant"]["id"]


async def create_product_and_variant(client: AsyncClient, token: str) -> tuple[str, str]:
    r = await client.post("/api/v1/products", json={
        "name": f"Prod {_uid8()}", "category": "CLOTHING", "base_price": "200.00",
        "variants": [{"name": "Default", "sku": f"SKU-{_uid8()}", "price": "200.00",
                       "stock_quantity": 500, "low_stock_alert": 5}],
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    pid = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/products/{pid}", headers=auth_headers(token))
    vid = r2.json()["data"]["variants"][0]["id"]
    return pid, vid


async def create_customer(client: AsyncClient, token: str) -> str:
    r = await client.post("/api/v1/customers", json={
        "name": f"Cust {_uid8()}", "phone": f"+88016{_uid8()}",
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


async def create_and_deliver_order(client: AsyncClient, token: str, cid: str, pid: str, vid: str) -> None:
    r = await client.post("/api/v1/orders", json={
        "customer_id": cid,
        "items": [{"product_id": pid, "variant_id": vid, "quantity": 1}],
        "payment_method": "COD",
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    oid = r.json()["data"]["id"]
    r2 = await client.post(f"/api/v1/orders/{oid}/payment",
                            json={"amount": "200", "method": "COD"}, headers=auth_headers(token))
    assert r2.status_code == 200, r2.text
    for status in ["CONFIRMED", "DELIVERED"]:
        r3 = await client.post(f"/api/v1/orders/{oid}/status",
                                json={"status": status}, headers=auth_headers(token))
        assert r3.status_code == 200, r3.text


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
async def merchant_a(client: AsyncClient):
    return await register_and_login(client, "strA")


@pytest.fixture
async def merchant_b(client: AsyncClient):
    return await register_and_login(client, "strB")


@pytest.fixture
async def setup_a(client: AsyncClient, merchant_a: tuple):
    """Creates 3 delivered+paid orders and 1 cancelled order for merchant A."""
    token, _ = merchant_a
    pid, vid = await create_product_and_variant(client, token)
    cid1 = await create_customer(client, token)
    cid2 = await create_customer(client, token)

    # 3 delivered + paid orders (cid1 becomes repeat customer)
    await create_and_deliver_order(client, token, cid1, pid, vid)
    await create_and_deliver_order(client, token, cid1, pid, vid)
    await create_and_deliver_order(client, token, cid2, pid, vid)

    # 1 cancelled order
    r = await client.post("/api/v1/orders", json={
        "customer_id": cid2,
        "items": [{"product_id": pid, "variant_id": vid, "quantity": 1}],
        "payment_method": "COD",
    }, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    await client.delete(f"/api/v1/orders/{r.json()['data']['id']}", headers=auth_headers(token))

    return token, pid, vid, cid1


# ── JWT Protection ────────────────────────────────────────────────

class TestJWTProtection:
    async def test_run_requires_auth(self, client: AsyncClient):
        assert (await client.post(f"{BASE}/run")).status_code == 401

    async def test_insights_requires_auth(self, client: AsyncClient):
        assert (await client.get(f"{BASE}/insights")).status_code == 401

    async def test_trust_score_requires_auth(self, client: AsyncClient):
        assert (await client.get(f"{BASE}/trust-score")).status_code == 401

    async def test_fraud_report_requires_auth(self, client: AsyncClient):
        assert (await client.get(f"{BASE}/fraud-report")).status_code == 401


# ── POST /run ─────────────────────────────────────────────────────

class TestRunAgents:
    async def test_run_returns_200(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_run_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        data = r.json()["data"]
        assert "trust" in data and "fraud" in data and "insights_saved" in data

    async def test_trust_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        trust = r.json()["data"]["trust"]
        assert "trust_score" in trust
        assert "confidence" in trust
        assert "risk_flags" in trust
        assert "details" in trust

    async def test_fraud_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        fraud = r.json()["data"]["fraud"]
        assert "fraud_risk_score" in fraud
        assert "alert_reasons" in fraud
        assert "details" in fraud

    async def test_trust_score_range(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        score = r.json()["data"]["trust"]["trust_score"]
        assert 0 <= score <= 100

    async def test_fraud_score_range(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        score = r.json()["data"]["fraud"]["fraud_risk_score"]
        assert 0 <= score <= 100

    async def test_confidence_valid_value(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        confidence = r.json()["data"]["trust"]["confidence"]
        assert confidence in ("LOW", "MEDIUM", "HIGH")

    async def test_insights_saved_is_2(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        assert r.json()["data"]["insights_saved"] == 2

    async def test_trust_score_positive_for_good_merchant(self, client: AsyncClient, setup_a: tuple):
        """3 delivered/paid orders → should produce above-baseline trust score."""
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        score = r.json()["data"]["trust"]["trust_score"]
        assert score > 50, f"Expected score > 50 for good merchant, got {score}"


# ── GET /insights ─────────────────────────────────────────────────

class TestListInsights:
    async def test_insights_empty_before_run(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get(f"{BASE}/insights", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["data"] == []

    async def test_insights_populated_after_run(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 2

    async def test_insights_schema(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights", headers=auth_headers(token))
        item = r.json()["data"][0]
        for f in ["id", "agent_name", "score", "payload", "created_at"]:
            assert f in item, f"Missing field: {f}"

    async def test_insights_filter_by_agent_name(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights?agent_name=trust_graph", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(item["agent_name"] == "trust_graph" for item in data)

    async def test_insights_filter_fraud_sentinel(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights?agent_name=fraud_sentinel", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(item["agent_name"] == "fraud_sentinel" for item in data)

    async def test_insights_limit(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        # run twice
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights?limit=1", headers=auth_headers(token))
        assert len(r.json()["data"]) <= 1


# ── GET /trust-score ──────────────────────────────────────────────

class TestTrustScore:
    async def test_trust_score_404_before_run(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get(f"{BASE}/trust-score", headers=auth_headers(token))
        assert r.status_code == 404

    async def test_trust_score_returns_200_after_run(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/trust-score", headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_trust_score_is_trust_agent(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/trust-score", headers=auth_headers(token))
        assert r.json()["data"]["agent_name"] == "trust_graph"

    async def test_trust_score_payload_has_score(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/trust-score", headers=auth_headers(token))
        payload = r.json()["data"]["payload"]
        assert "trust_score" in payload


# ── GET /fraud-report ─────────────────────────────────────────────

class TestFraudReport:
    async def test_fraud_report_404_before_run(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get(f"{BASE}/fraud-report", headers=auth_headers(token))
        assert r.status_code == 404

    async def test_fraud_report_returns_200_after_run(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/fraud-report", headers=auth_headers(token))
        assert r.status_code == 200, r.text

    async def test_fraud_report_is_fraud_agent(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/fraud-report", headers=auth_headers(token))
        assert r.json()["data"]["agent_name"] == "fraud_sentinel"

    async def test_fraud_report_payload_has_score(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/fraud-report", headers=auth_headers(token))
        payload = r.json()["data"]["payload"]
        assert "fraud_risk_score" in payload


# ── Trust Scoring Logic ───────────────────────────────────────────

class TestTrustScoringLogic:
    async def test_low_confidence_for_new_merchant(self, client: AsyncClient, merchant_b: tuple):
        token, _ = merchant_b
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        assert r.json()["data"]["trust"]["confidence"] == "LOW"

    async def test_details_contains_rates(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        details = r.json()["data"]["trust"]["details"]
        for f in ["total_orders", "delivered_orders", "delivery_rate",
                   "payment_rate", "cancellation_rate"]:
            assert f in details, f"Missing detail: {f}"

    async def test_risk_flags_is_list(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        r = await client.post(f"{BASE}/run", headers=auth_headers(token))
        assert isinstance(r.json()["data"]["trust"]["risk_flags"], list)


# ── Merchant Isolation ────────────────────────────────────────────

class TestMerchantIsolation:
    async def test_insights_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        token_a, *_ = setup_a
        token_b, _ = merchant_b
        # Run as A
        await client.post(f"{BASE}/run", headers=auth_headers(token_a))
        # B should see no insights
        r = await client.get(f"{BASE}/insights", headers=auth_headers(token_b))
        assert r.json()["data"] == []

    async def test_trust_score_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        token_a, *_ = setup_a
        token_b, _ = merchant_b
        await client.post(f"{BASE}/run", headers=auth_headers(token_a))
        r = await client.get(f"{BASE}/trust-score", headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_fraud_report_isolated(self, client: AsyncClient, setup_a: tuple, merchant_b: tuple):
        token_a, *_ = setup_a
        token_b, _ = merchant_b
        await client.post(f"{BASE}/run", headers=auth_headers(token_a))
        r = await client.get(f"{BASE}/fraud-report", headers=auth_headers(token_b))
        assert r.status_code == 404

    async def test_run_twice_accumulates_insights(self, client: AsyncClient, setup_a: tuple):
        token, *_ = setup_a
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        await client.post(f"{BASE}/run", headers=auth_headers(token))
        r = await client.get(f"{BASE}/insights", headers=auth_headers(token))
        assert len(r.json()["data"]) >= 4  # 2 per run × 2 runs
