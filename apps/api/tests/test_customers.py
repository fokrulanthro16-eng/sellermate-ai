"""
Customer module integration tests.
Covers: all 8 endpoints, merchant isolation, security, tags, search/filter, pagination, CSV export.
"""

import uuid
import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────

def _uid8() -> str:
    """8 guaranteed-unique decimal digits from a UUID4 int."""
    return f"{uuid.uuid4().int % 100_000_000:08d}"


async def register_and_login(client: AsyncClient, suffix: str) -> tuple[str, str]:
    digits = _uid8()
    phone = f"+88015{digits}"
    payload = {
        "email": f"cust{suffix}{digits}@test.com",
        "phone": phone,
        "password": "TestPass1!",
        "business_name": f"Cust Biz {suffix}",
        "owner_name": f"Owner {suffix}",
        "business_type": "FASHION_CLOTHING",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"

    r = await client.post("/api/v1/auth/login", json={"identifier": phone, "password": "TestPass1!"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    return d["tokens"]["access_token"], d["merchant"]["id"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
async def merchant_a(client: AsyncClient):
    return await register_and_login(client, "ma")


@pytest.fixture
async def merchant_b(client: AsyncClient):
    return await register_and_login(client, "mb")


@pytest.fixture
async def customer_a(client: AsyncClient, merchant_a: tuple):
    token, _ = merchant_a
    phone = f"+88016{_uid8()}"
    r = await client.post(
        "/api/v1/customers",
        json={
            "name": "Alice Rahman",
            "phone": phone,
            "email": "alice@example.com",
            "district": "Dhaka",
            "division": "Dhaka",
            "notes": "Main test customer",
            "tags": ["vip", "regular"],
            "source": "MANUAL",
        },
        headers=headers(token),
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ── JWT Protection ────────────────────────────────────────────────

class TestJWTProtection:
    FAKE_ID = "00000000-0000-0000-0000-000000000000"

    async def test_list_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/customers")
        assert r.status_code == 401

    async def test_create_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/customers", json={"name": "x", "phone": "+8801512345678"})
        assert r.status_code == 401

    async def test_export_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/customers/export")
        assert r.status_code == 401

    async def test_get_requires_auth(self, client: AsyncClient):
        r = await client.get(f"/api/v1/customers/{self.FAKE_ID}")
        assert r.status_code == 401

    async def test_patch_requires_auth(self, client: AsyncClient):
        r = await client.patch(f"/api/v1/customers/{self.FAKE_ID}", json={"name": "x"})
        assert r.status_code == 401

    async def test_delete_requires_auth(self, client: AsyncClient):
        r = await client.delete(f"/api/v1/customers/{self.FAKE_ID}")
        assert r.status_code == 401

    async def test_add_tag_requires_auth(self, client: AsyncClient):
        r = await client.post(f"/api/v1/customers/{self.FAKE_ID}/tags/vip")
        assert r.status_code == 401

    async def test_remove_tag_requires_auth(self, client: AsyncClient):
        r = await client.delete(f"/api/v1/customers/{self.FAKE_ID}/tags/vip")
        assert r.status_code == 401


# ── Create Customer ───────────────────────────────────────────────

class TestCreateCustomer:
    async def test_create_returns_201(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"name": "New Customer", "phone": f"+88017{_uid8()}"},
            headers=headers(token),
        )
        assert r.status_code == 201

    async def test_create_response_schema(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        required = ["id", "merchant_id", "name", "phone", "total_orders",
                    "total_spent", "tags", "source", "created_at", "updated_at"]
        for field in required:
            assert field in customer_a, f"Missing field: {field}"

    async def test_create_defaults(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        assert customer_a["total_orders"] == 0
        assert float(customer_a["total_spent"]) == 0.0
        assert customer_a["source"] == "MANUAL"

    async def test_create_tags_stored(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        assert set(customer_a["tags"]) == {"vip", "regular"}

    async def test_create_source_whatsapp(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"name": "WA Customer", "phone": f"+88018{_uid8()}", "source": "WHATSAPP"},
            headers=headers(token),
        )
        assert r.status_code == 201
        assert r.json()["data"]["source"] == "WHATSAPP"

    async def test_duplicate_phone_returns_409(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"name": "Clone", "phone": customer_a["phone"]},
            headers=headers(token),
        )
        assert r.status_code == 409

    async def test_invalid_phone_returns_422(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"name": "Bad", "phone": "not-a-phone"},
            headers=headers(token),
        )
        assert r.status_code == 422

    async def test_missing_name_returns_422(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"phone": "+8801512345678"},
            headers=headers(token),
        )
        assert r.status_code == 422

    async def test_same_phone_different_merchants_allowed(
        self, client: AsyncClient, merchant_a: tuple, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.post(
            "/api/v1/customers",
            json={"name": "MB Customer", "phone": customer_a["phone"]},
            headers=headers(token_b),
        )
        assert r.status_code == 201


# ── Get Customer ──────────────────────────────────────────────────

class TestGetCustomer:
    async def test_get_by_id(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["id"] == customer_a["id"]

    async def test_unknown_id_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.get(
            "/api/v1/customers/00000000-0000-0000-0000-000000000001",
            headers=headers(token),
        )
        assert r.status_code == 404


# ── Update Customer ───────────────────────────────────────────────

class TestUpdateCustomer:
    async def test_update_name(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"name": "Updated Name"},
            headers=headers(token),
        )
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "Updated Name"

    async def test_update_district(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"district": "Chittagong"},
            headers=headers(token),
        )
        assert r.status_code == 200
        assert r.json()["data"]["district"] == "Chittagong"

    async def test_update_notes(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"notes": "updated notes"},
            headers=headers(token),
        )
        assert r.status_code == 200
        assert r.json()["data"]["notes"] == "updated notes"

    async def test_update_nonexistent_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.patch(
            "/api/v1/customers/00000000-0000-0000-0000-000000000001",
            json={"name": "x"},
            headers=headers(token),
        )
        assert r.status_code == 404


# ── Delete Customer ───────────────────────────────────────────────

class TestDeleteCustomer:
    async def test_delete_customer(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.post(
            "/api/v1/customers",
            json={"name": "To Delete", "phone": f"+88019{_uid8()}"},
            headers=headers(token),
        )
        assert r.status_code == 201
        cid = r.json()["data"]["id"]

        r_del = await client.delete(f"/api/v1/customers/{cid}", headers=headers(token))
        assert r_del.status_code == 200
        assert "message" in r_del.json()

        r_get = await client.get(f"/api/v1/customers/{cid}", headers=headers(token))
        assert r_get.status_code == 404

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient, merchant_a: tuple):
        token, _ = merchant_a
        r = await client.delete(
            "/api/v1/customers/00000000-0000-0000-0000-000000000001",
            headers=headers(token),
        )
        assert r.status_code == 404


# ── List Customers ────────────────────────────────────────────────

class TestListCustomers:
    async def test_list_returns_200(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers", headers=headers(token))
        assert r.status_code == 200

    async def test_list_has_pagination_meta(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers", headers=headers(token))
        meta = r.json().get("meta", {})
        for key in ["page", "limit", "total", "total_pages"]:
            assert key in meta, f"Missing meta key: {key}"

    async def test_list_contains_created_customer(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers", headers=headers(token))
        ids = [c["id"] for c in r.json()["data"]]
        assert customer_a["id"] in ids

    async def test_pagination_limit(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers?limit=1", headers=headers(token))
        assert r.status_code == 200
        assert len(r.json()["data"]) <= 1
        assert r.json()["meta"]["limit"] == 1

    async def test_search_by_name(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers?search=Alice", headers=headers(token))
        assert r.status_code == 200
        results = r.json()["data"]
        assert any("alice" in c["name"].lower() for c in results)

    async def test_search_no_match_empty(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers?search=xyznotexist999", headers=headers(token))
        assert r.status_code == 200
        assert len(r.json()["data"]) == 0

    async def test_district_filter(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers?district=Dhaka", headers=headers(token))
        assert r.status_code == 200
        results = r.json()["data"]
        assert all(c["district"] == "Dhaka" for c in results if c["district"])

    async def test_tags_filter(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        """Bug 1 fix: tags filter was dead code before; verify it now works."""
        token, _ = merchant_a
        r = await client.get("/api/v1/customers?tags=vip", headers=headers(token))
        assert r.status_code == 200
        results = r.json()["data"]
        assert len(results) >= 1
        assert all("vip" in c["tags"] for c in results)

    async def test_tags_filter_excludes_non_matching(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.post(
            "/api/v1/customers",
            json={"name": "Wholesale Only", "phone": f"+88013{_uid8()}", "tags": ["wholesale"]},
            headers=headers(token),
        )
        r = await client.get("/api/v1/customers?tags=vip", headers=headers(token))
        results = r.json()["data"]
        non_vip = [c for c in results if "vip" not in c["tags"]]
        assert len(non_vip) == 0

    async def test_page_2(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.post(
            "/api/v1/customers",
            json={"name": "Page2 Customer", "phone": f"+88014{_uid8()}"},
            headers=headers(token),
        )
        r1 = await client.get("/api/v1/customers?page=1&limit=1", headers=headers(token))
        r2 = await client.get("/api/v1/customers?page=2&limit=1", headers=headers(token))
        assert r1.status_code == 200
        assert r2.status_code == 200
        ids_p1 = {c["id"] for c in r1.json()["data"]}
        ids_p2 = {c["id"] for c in r2.json()["data"]}
        # Pages must not overlap
        assert ids_p1.isdisjoint(ids_p2)


# ── Tags Management ───────────────────────────────────────────────

class TestTagsManagement:
    async def test_add_tag(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.post(
            f"/api/v1/customers/{customer_a['id']}/tags/premium",
            headers=headers(token),
        )
        assert r.status_code == 200
        assert "premium" in r.json()["data"]["tags"]

    async def test_add_tag_preserves_existing(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.post(
            f"/api/v1/customers/{customer_a['id']}/tags/newone",
            headers=headers(token),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        tags = r.json()["data"]["tags"]
        assert "vip" in tags
        assert "regular" in tags
        assert "newone" in tags

    async def test_add_duplicate_tag_idempotent(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.post(
            f"/api/v1/customers/{customer_a['id']}/tags/vip",
            headers=headers(token),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        tags = r.json()["data"]["tags"]
        assert tags.count("vip") == 1

    async def test_remove_tag(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.delete(
            f"/api/v1/customers/{customer_a['id']}/tags/regular",
            headers=headers(token),
        )
        assert r.status_code == 200
        assert "regular" not in r.json()["data"]["tags"]

    async def test_remove_tag_preserves_others(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.delete(
            f"/api/v1/customers/{customer_a['id']}/tags/vip",
            headers=headers(token),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        tags = r.json()["data"]["tags"]
        assert "regular" in tags
        assert "vip" not in tags

    async def test_remove_nonexistent_tag_ok(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.delete(
            f"/api/v1/customers/{customer_a['id']}/tags/doesnotexist",
            headers=headers(token),
        )
        assert r.status_code == 200


# ── CSV Export ────────────────────────────────────────────────────

class TestCSVExport:
    async def test_export_returns_200(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers/export", headers=headers(token))
        assert r.status_code == 200

    async def test_export_content_type_csv(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers/export", headers=headers(token))
        assert "text/csv" in r.headers.get("content-type", "")

    async def test_export_has_header_row(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers/export", headers=headers(token))
        text = r.content.decode("utf-8-sig")
        assert "name" in text.lower()
        assert "phone" in text.lower()

    async def test_export_contains_customer_data(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        r = await client.get("/api/v1/customers/export", headers=headers(token))
        text = r.content.decode("utf-8-sig")
        assert "Alice" in text


# ── Merchant Isolation ────────────────────────────────────────────

class TestMerchantIsolation:
    async def test_list_excludes_other_merchant_customers(
        self, client: AsyncClient, merchant_a: tuple, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.get("/api/v1/customers", headers=headers(token_b))
        ids = [c["id"] for c in r.json()["data"]]
        assert customer_a["id"] not in ids

    async def test_get_other_merchant_customer_returns_404(
        self, client: AsyncClient, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token_b))
        assert r.status_code == 404

    async def test_patch_other_merchant_customer_returns_404(
        self, client: AsyncClient, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"name": "Hacked"},
            headers=headers(token_b),
        )
        assert r.status_code == 404

    async def test_delete_other_merchant_customer_returns_404(
        self, client: AsyncClient, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.delete(f"/api/v1/customers/{customer_a['id']}", headers=headers(token_b))
        assert r.status_code == 404

    async def test_add_tag_other_merchant_returns_404(
        self, client: AsyncClient, merchant_b: tuple, customer_a: dict
    ):
        token_b, _ = merchant_b
        r = await client.post(
            f"/api/v1/customers/{customer_a['id']}/tags/hack",
            headers=headers(token_b),
        )
        assert r.status_code == 404

    async def test_cross_merchant_attack_does_not_modify(
        self, client: AsyncClient, merchant_a: tuple, merchant_b: tuple, customer_a: dict
    ):
        token_a, _ = merchant_a
        token_b, _ = merchant_b
        await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"name": "Hacked By B"},
            headers=headers(token_b),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token_a))
        assert r.json()["data"]["name"] == "Alice Rahman"


# ── DB Persistence ────────────────────────────────────────────────

class TestDBPersistence:
    async def test_customer_persists_across_requests(
        self, client: AsyncClient, merchant_a: tuple, customer_a: dict
    ):
        token, _ = merchant_a
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        assert r.status_code == 200
        assert r.json()["data"]["id"] == customer_a["id"]

    async def test_update_persists(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.patch(
            f"/api/v1/customers/{customer_a['id']}",
            json={"notes": "persistence check"},
            headers=headers(token),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        assert r.json()["data"]["notes"] == "persistence check"

    async def test_tags_persist_after_add(self, client: AsyncClient, merchant_a: tuple, customer_a: dict):
        token, _ = merchant_a
        await client.post(
            f"/api/v1/customers/{customer_a['id']}/tags/persistent",
            headers=headers(token),
        )
        r = await client.get(f"/api/v1/customers/{customer_a['id']}", headers=headers(token))
        assert "persistent" in r.json()["data"]["tags"]
