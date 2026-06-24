"""Product module integration tests — pytest coverage."""
import pytest
from httpx import AsyncClient

PROD = "/api/v1/products"


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def merchant_a(client: AsyncClient):
    """Register merchant A and return token."""
    r = await client.post("/api/v1/auth/register", json={
        "email": "prod_a@test.com",
        "phone": "+8801700000001",
        "password": "Test1234!",
        "business_name": "Product Shop A",
        "owner_name": "Owner A",
        "business_type": "ELECTRONICS",
    })
    tokens = r.json().get("data", {}).get("tokens", {})
    return tokens.get("access_token", "")


@pytest.fixture
async def merchant_b(client: AsyncClient):
    """Register merchant B for isolation tests."""
    r = await client.post("/api/v1/auth/register", json={
        "email": "prod_b@test.com",
        "phone": "+8801700000002",
        "password": "Test1234!",
        "business_name": "Product Shop B",
        "owner_name": "Owner B",
        "business_type": "FASHION_CLOTHING",
    })
    tokens = r.json().get("data", {}).get("tokens", {})
    return tokens.get("access_token", "")


@pytest.fixture
async def product_a(client: AsyncClient, merchant_a: str):
    """Create a product for merchant A and return its data."""
    r = await client.post(PROD, json={
        "name": "Fixture Widget",
        "category": "Electronics",
        "base_price": 500,
        "sku": "FW-001",
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    return r.json()["data"]


@pytest.fixture
async def product_with_variants(client: AsyncClient, merchant_a: str):
    """Create a product with 2 variants."""
    r = await client.post(PROD, json={
        "name": "Variant Product",
        "category": "Fashion",
        "base_price": 300,
        "sku": "VP-001",
        "variants": [
            {"name": "Red S", "attributes": {"color": "red", "size": "S"}, "stock_quantity": 10},
            {"name": "Blue L", "attributes": {"color": "blue", "size": "L"}, "stock_quantity": 5},
        ],
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    return r.json()["data"]


# ── T01: JWT protection ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_product_jwt_protection(client: AsyncClient):
    endpoints = [
        ("GET",    f"{PROD}"),
        ("POST",   f"{PROD}"),
        ("GET",    f"{PROD}/categories"),
        ("GET",    f"{PROD}/some-id"),
        ("PATCH",  f"{PROD}/some-id"),
        ("DELETE", f"{PROD}/some-id"),
        ("POST",   f"{PROD}/some-id/variants"),
        ("PATCH",  f"{PROD}/some-id/variants/some-vid"),
        ("DELETE", f"{PROD}/some-id/variants/some-vid"),
    ]
    for method, path in endpoints:
        resp = await client.request(method, path, json={"name": "x"})
        assert resp.status_code == 401, f"{method} {path} should be 401 without token"


# ── T02: Create product ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_product_minimal(client: AsyncClient, merchant_a: str):
    r = await client.post(PROD, json={
        "name": "Simple Product",
        "category": "General",
        "base_price": 100,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["name"] == "Simple Product"
    assert data["category"] == "General"
    assert str(data["base_price"]) in ("100", "100.00")
    assert data["is_active"] is True
    assert data["is_published"] is False
    assert data["total_sold"] == 0
    assert data["image_urls"] == []
    assert "id" in data
    assert "merchant_id" in data


@pytest.mark.asyncio
async def test_create_product_full(client: AsyncClient, merchant_a: str):
    r = await client.post(PROD, json={
        "name": "Full Product",
        "name_bangla": "সম্পূর্ণ পণ্য",
        "description": "A full product",
        "description_bangla": "একটি সম্পূর্ণ পণ্য",
        "category": "Electronics",
        "sku": "FULL-001",
        "base_price": 999,
        "sale_price": 799,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["name_bangla"] == "সম্পূর্ণ পণ্য"
    assert data["sku"] == "FULL-001"
    assert str(data["sale_price"]) in ("799", "799.00")


@pytest.mark.asyncio
async def test_create_product_with_inline_variants(client: AsyncClient, merchant_a: str, product_with_variants: dict):
    # product_with_variants fixture already asserts 201; just verify structure
    assert product_with_variants["name"] == "Variant Product"
    assert product_with_variants["sku"] == "VP-001"
    # Variants are in the product detail, not in the list response — GET by ID
    r = await client.get(f"{PROD}/{product_with_variants['id']}",
                         headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    variants = r.json()["data"]["variants"]
    assert len(variants) == 2
    names = {v["name"] for v in variants}
    assert names == {"Red S", "Blue L"}


@pytest.mark.asyncio
async def test_create_product_duplicate_sku_returns_409(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.post(PROD, json={
        "name": "Another Widget",
        "category": "Electronics",
        "base_price": 200,
        "sku": "FW-001",  # same SKU as product_a
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_product_invalid_price(client: AsyncClient, merchant_a: str):
    r = await client.post(PROD, json={
        "name": "Zero Price",
        "category": "General",
        "base_price": 0,  # must be > 0
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 422


# ── T03: List products ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient, merchant_a: str, product_a: dict, product_with_variants: dict):
    r = await client.get(PROD, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "data" in body
    assert "meta" in body
    meta = body["meta"]
    assert meta["page"] == 1
    assert meta["limit"] == 20
    assert meta["total"] >= 2
    assert "total_pages" in meta


@pytest.mark.asyncio
async def test_list_products_limit(client: AsyncClient, merchant_a: str, product_a: dict, product_with_variants: dict):
    r = await client.get(f"{PROD}?page=1&limit=1", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1
    assert r.json()["meta"]["limit"] == 1


@pytest.mark.asyncio
async def test_list_products_search(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.get(f"{PROD}?search=Fixture", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert all("Fixture" in p["name"] for p in data)


@pytest.mark.asyncio
async def test_list_products_search_no_match(client: AsyncClient, merchant_a: str):
    r = await client.get(f"{PROD}?search=xyz_nonexistent_abc", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    assert r.json()["data"] == []
    assert r.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_products_category_filter(client: AsyncClient, merchant_a: str, product_a: dict, product_with_variants: dict):
    r = await client.get(f"{PROD}?category=Electronics", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert all(p["category"] == "Electronics" for p in data)


@pytest.mark.asyncio
async def test_list_products_excludes_inactive_by_default(client: AsyncClient, merchant_a: str, product_a: dict):
    # Delete the product (soft delete)
    await client.delete(f"{PROD}/{product_a['id']}",
                        headers={"Authorization": f"Bearer {merchant_a}"})
    # Default list should not include it
    r = await client.get(PROD, headers={"Authorization": f"Bearer {merchant_a}"})
    ids = [p["id"] for p in r.json()["data"]]
    assert product_a["id"] not in ids


@pytest.mark.asyncio
async def test_list_products_is_active_false_shows_deleted(client: AsyncClient, merchant_a: str, product_a: dict):
    await client.delete(f"{PROD}/{product_a['id']}",
                        headers={"Authorization": f"Bearer {merchant_a}"})
    r = await client.get(f"{PROD}?is_active=false", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["data"]]
    assert product_a["id"] in ids


# ── T04: Get product by ID ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_product_with_variants(client: AsyncClient, merchant_a: str, product_with_variants: dict):
    r = await client.get(f"{PROD}/{product_with_variants['id']}",
                         headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] == product_with_variants["id"]
    assert "variants" in data
    assert len(data["variants"]) == 2


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient, merchant_a: str):
    r = await client.get(f"{PROD}/00000000-0000-0000-0000-000000000000",
                         headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 404


# ── T05: Update product ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.patch(f"{PROD}/{product_a['id']}", json={
        "name": "Updated Widget",
        "sale_price": 450,
        "is_published": True,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "Updated Widget"
    assert str(data["sale_price"]) in ("450", "450.00")
    assert data["is_published"] is True
    # Unchanged fields preserved
    assert data["category"] == "Electronics"


@pytest.mark.asyncio
async def test_update_deleted_product_returns_404(client: AsyncClient, merchant_a: str, product_a: dict):
    await client.delete(f"{PROD}/{product_a['id']}",
                        headers={"Authorization": f"Bearer {merchant_a}"})
    r = await client.patch(f"{PROD}/{product_a['id']}", json={"name": "Ghost"},
                           headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 404


# ── T06: Delete product ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_product_soft(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.delete(f"{PROD}/{product_a['id']}",
                            headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 204

    # GET returns 404 after soft delete
    r2 = await client.get(f"{PROD}/{product_a['id']}",
                          headers={"Authorization": f"Bearer {merchant_a}"})
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_product(client: AsyncClient, merchant_a: str):
    r = await client.delete(f"{PROD}/00000000-0000-0000-0000-000000000000",
                            headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 404


# ── T07: Variants ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_variant(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.post(f"{PROD}/{product_a['id']}/variants", json={
        "name": "Green M",
        "attributes": {"color": "green", "size": "M"},
        "stock_quantity": 20,
        "low_stock_alert": 3,
        "price": 480,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    v = r.json()["data"]
    assert v["product_id"] == product_a["id"]
    assert v["name"] == "Green M"
    assert v["stock_quantity"] == 20
    assert v["low_stock_alert"] == 3
    assert str(v["price"]) in ("480", "480.00")
    assert v["attributes"] == {"color": "green", "size": "M"}


@pytest.mark.asyncio
async def test_add_variant_to_deleted_product_returns_404(client: AsyncClient, merchant_a: str, product_a: dict):
    await client.delete(f"{PROD}/{product_a['id']}",
                        headers={"Authorization": f"Bearer {merchant_a}"})
    r = await client.post(f"{PROD}/{product_a['id']}/variants", json={
        "name": "Ghost Variant", "stock_quantity": 0,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_variant(client: AsyncClient, merchant_a: str, product_with_variants: dict):
    r_detail = await client.get(f"{PROD}/{product_with_variants['id']}",
                                headers={"Authorization": f"Bearer {merchant_a}"})
    variant_id = r_detail.json()["data"]["variants"][0]["id"]

    r = await client.patch(f"{PROD}/{product_with_variants['id']}/variants/{variant_id}", json={
        "stock_quantity": 99,
        "name": "Patched Variant",
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    assert r.json()["data"]["stock_quantity"] == 99
    assert r.json()["data"]["name"] == "Patched Variant"


@pytest.mark.asyncio
async def test_delete_variant(client: AsyncClient, merchant_a: str, product_with_variants: dict):
    r_detail = await client.get(f"{PROD}/{product_with_variants['id']}",
                                headers={"Authorization": f"Bearer {merchant_a}"})
    variant_id = r_detail.json()["data"]["variants"][0]["id"]

    r = await client.delete(f"{PROD}/{product_with_variants['id']}/variants/{variant_id}",
                             headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 204

    # Verify it's gone
    r2 = await client.get(f"{PROD}/{product_with_variants['id']}",
                          headers={"Authorization": f"Bearer {merchant_a}"})
    variant_ids = [v["id"] for v in r2.json()["data"]["variants"]]
    assert variant_id not in variant_ids


@pytest.mark.asyncio
async def test_update_variant_not_found(client: AsyncClient, merchant_a: str, product_a: dict):
    r = await client.patch(f"{PROD}/{product_a['id']}/variants/00000000-0000-0000-0000-000000000000", json={
        "stock_quantity": 5,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 404


# ── T08: Categories ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient, merchant_a: str, product_a: dict, product_with_variants: dict):
    r = await client.get(f"{PROD}/categories", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    cats = r.json()["data"]
    assert isinstance(cats, list)
    assert "Electronics" in cats
    assert "Fashion" in cats
    # Sorted alphabetically
    assert cats == sorted(cats)


@pytest.mark.asyncio
async def test_categories_empty_for_new_merchant(client: AsyncClient, merchant_b: str):
    r = await client.get(f"{PROD}/categories", headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 200
    assert r.json()["data"] == []


# ── T09: Merchant isolation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_merchant_isolation_get(client: AsyncClient, merchant_a: str, merchant_b: str, product_a: dict):
    r = await client.get(f"{PROD}/{product_a['id']}",
                         headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_merchant_isolation_patch(client: AsyncClient, merchant_a: str, merchant_b: str, product_a: dict):
    r = await client.patch(f"{PROD}/{product_a['id']}", json={"name": "Hijacked"},
                           headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 404
    # Verify name unchanged
    r2 = await client.get(f"{PROD}/{product_a['id']}",
                          headers={"Authorization": f"Bearer {merchant_a}"})
    assert r2.json()["data"]["name"] == "Fixture Widget"


@pytest.mark.asyncio
async def test_merchant_isolation_delete(client: AsyncClient, merchant_a: str, merchant_b: str, product_a: dict):
    r = await client.delete(f"{PROD}/{product_a['id']}",
                            headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 404
    # Product still accessible by owner
    r2 = await client.get(f"{PROD}/{product_a['id']}",
                          headers={"Authorization": f"Bearer {merchant_a}"})
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_merchant_isolation_add_variant(client: AsyncClient, merchant_a: str, merchant_b: str, product_a: dict):
    r = await client.post(f"{PROD}/{product_a['id']}/variants", json={
        "name": "Injected Variant", "stock_quantity": 100,
    }, headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_merchant_list_isolation(client: AsyncClient, merchant_a: str, merchant_b: str, product_a: dict):
    """Merchant B's product list must not contain Merchant A's products."""
    r = await client.get(PROD, headers={"Authorization": f"Bearer {merchant_b}"})
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["data"]]
    assert product_a["id"] not in ids


# ── T10: DB persistence ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_db_persistence_full_cycle(client: AsyncClient, merchant_a: str):
    """Create → read back → update → read back — all data persists correctly."""
    create_r = await client.post(PROD, json={
        "name": "Persistence Test",
        "name_bangla": "স্থায়িত্ব পরীক্ষা",
        "description": "Test persistence",
        "category": "TestCat",
        "sku": "PERSIST-001",
        "base_price": 750,
        "sale_price": 600,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert create_r.status_code == 201
    pid = create_r.json()["data"]["id"]

    # Read back immediately
    r = await client.get(f"{PROD}/{pid}", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["name"] == "Persistence Test"
    assert d["name_bangla"] == "স্থায়িত্ব পরীক্ষা"
    assert d["sku"] == "PERSIST-001"
    assert str(d["base_price"]) in ("750", "750.00")
    assert str(d["sale_price"]) in ("600", "600.00")

    # Update
    await client.patch(f"{PROD}/{pid}", json={"name": "Updated Persistence"},
                       headers={"Authorization": f"Bearer {merchant_a}"})

    # Read back updated
    r2 = await client.get(f"{PROD}/{pid}", headers={"Authorization": f"Bearer {merchant_a}"})
    assert r2.json()["data"]["name"] == "Updated Persistence"
    # Other fields unchanged
    assert r2.json()["data"]["sku"] == "PERSIST-001"


# ── T11: Inventory linkage ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_inventory_stock_persists_on_variant(client: AsyncClient, merchant_a: str, product_a: dict):
    """Variant stock_quantity is stored and retrievable."""
    r = await client.post(f"{PROD}/{product_a['id']}/variants", json={
        "name": "Stock Test Variant",
        "stock_quantity": 42,
        "low_stock_alert": 7,
    }, headers={"Authorization": f"Bearer {merchant_a}"})
    assert r.status_code == 201
    vid = r.json()["data"]["id"]

    # Verify via product detail
    detail_r = await client.get(f"{PROD}/{product_a['id']}",
                                headers={"Authorization": f"Bearer {merchant_a}"})
    variants = detail_r.json()["data"]["variants"]
    stock_variant = next((v for v in variants if v["id"] == vid), None)
    assert stock_variant is not None
    assert stock_variant["stock_quantity"] == 42
    assert stock_variant["low_stock_alert"] == 7

    # Update stock
    await client.patch(f"{PROD}/{product_a['id']}/variants/{vid}", json={"stock_quantity": 20},
                       headers={"Authorization": f"Bearer {merchant_a}"})

    # Verify updated stock persists
    detail_r2 = await client.get(f"{PROD}/{product_a['id']}",
                                 headers={"Authorization": f"Bearer {merchant_a}"})
    updated = next((v for v in detail_r2.json()["data"]["variants"] if v["id"] == vid), None)
    assert updated["stock_quantity"] == 20
