"""Public (unauthenticated) storefront and marketplace endpoints."""
from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException, OutOfStockException
from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import (
    Order,
    OrderChannel,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.models.product import Product, ProductVariant
from app.services import inventory_service

router = APIRouter()
DB = Depends(get_db)


# ── Request schemas ────────────────────────────────────────────────────────────

class _PublicOrderItem(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=36)
    variant_id: Optional[str] = Field(None, max_length=36)
    quantity: int = Field(1, ge=1, le=999)


class _PublicOrderRequest(BaseModel):
    merchant_id: str = Field(..., min_length=1, max_length=36)
    customer_name: str = Field("Buyer", max_length=100)
    customer_phone: str = Field(..., min_length=5, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=200)
    delivery_address: str = Field(..., min_length=3, max_length=500)
    delivery_district: Optional[str] = Field(None, max_length=100)
    delivery_charge: float = Field(60.0, ge=0, le=10_000)
    payment_method: str = Field("COD", max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    items: list[_PublicOrderItem] = Field(..., min_length=1, max_length=50)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _product_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "merchant_id": p.merchant_id,
        "name": p.name,
        "name_bangla": p.name_bangla,
        "description": p.description,
        "category": p.category,
        "base_price": float(p.base_price),
        "sale_price": float(p.sale_price) if p.sale_price else None,
        "image_urls": p.image_urls or [],
        "total_sold": p.total_sold,
    }


def _store_dict(m: Merchant, product_count: int = 0) -> dict:
    return {
        "id": m.id,
        "store_slug": m.store_slug,
        "business_name": m.business_name,
        "store_description": m.store_description,
        "store_banner_url": m.store_banner_url,
        "logo_url": m.logo_url,
        "district": m.district,
        "latitude": m.latitude,
        "longitude": m.longitude,
        "product_count": product_count,
    }


def _order_detail(order: Order) -> dict:
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "total_amount": float(order.total_amount),
        "paid_amount": float(order.paid_amount),
        "due_amount": float(order.due_amount),
        "courier_name": order.courier_name,
        "tracking_number": order.tracking_number,
        "delivery_address": order.delivery_address,
        "delivery_district": order.delivery_district,
        "notes": order.notes,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/stores")
async def list_stores(
    search: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = DB,
) -> dict:
    q = select(Merchant).where(Merchant.store_slug.isnot(None), Merchant.status == "ACTIVE")
    if search:
        q = q.where(Merchant.business_name.ilike(f"%{search}%"))
    if district:
        q = q.where(Merchant.district.ilike(f"%{district}%"))
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    merchants = result.scalars().all()

    counts: dict = {}
    if merchants:
        ids = [m.id for m in merchants]
        count_q = (
            select(Product.merchant_id, func.count().label("cnt"))
            .where(Product.merchant_id.in_(ids), Product.is_published.is_(True))
            .group_by(Product.merchant_id)
        )
        count_rows = (await db.execute(count_q)).all()
        counts = {row.merchant_id: row.cnt for row in count_rows}

    return {"success": True, "data": {"stores": [_store_dict(m, counts.get(m.id, 0)) for m in merchants]}}


@router.get("/stores/{slug}")
async def get_store(slug: str, db: AsyncSession = DB) -> dict:
    result = await db.execute(select(Merchant).where(Merchant.store_slug == slug))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise NotFoundException("Store not found")
    count_r = await db.execute(
        select(func.count()).where(Product.merchant_id == merchant.id, Product.is_published.is_(True))
    )
    count = count_r.scalar() or 0
    return {"success": True, "data": _store_dict(merchant, count)}


@router.get("/stores/{slug}/products")
async def get_store_products(
    slug: str,
    category: Optional[str] = Query(None),
    limit: int = Query(24, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = DB,
) -> dict:
    m_result = await db.execute(select(Merchant).where(Merchant.store_slug == slug))
    merchant = m_result.scalar_one_or_none()
    if not merchant:
        raise NotFoundException("Store not found")

    q = select(Product).where(Product.merchant_id == merchant.id, Product.is_published.is_(True))
    if category:
        q = q.where(Product.category.ilike(f"%{category}%"))
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    products = result.scalars().all()
    return {"success": True, "data": {"products": [_product_dict(p) for p in products]}}


@router.get(
    "/search",
    dependencies=[Depends(rate_limiter("pub_search", max_calls=30, window_seconds=60))],
)
async def search_products(
    q: str = Query("", min_length=1),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(24, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = DB,
) -> dict:
    stmt = select(Product).where(Product.is_published.is_(True))
    if q:
        stmt = stmt.where(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.name_bangla.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
            )
        )
    if category:
        stmt = stmt.where(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        stmt = stmt.where(Product.base_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.base_price <= max_price)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return {"success": True, "data": {"products": [_product_dict(p) for p in products], "query": q}}


@router.get("/nearby")
async def nearby_stores(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(10.0, le=50),
    limit: int = Query(20, le=50),
    db: AsyncSession = DB,
) -> dict:
    import math

    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * abs(math.cos(math.radians(lat))) or 1)
    q = select(Merchant).where(
        Merchant.latitude.isnot(None),
        Merchant.longitude.isnot(None),
        Merchant.latitude.between(lat - lat_delta, lat + lat_delta),
        Merchant.longitude.between(lng - lng_delta, lng + lng_delta),
        Merchant.status == "ACTIVE",
    ).limit(limit)
    result = await db.execute(q)
    merchants = result.scalars().all()
    return {"success": True, "data": {"stores": [_store_dict(m) for m in merchants]}}


@router.post(
    "/orders",
    dependencies=[Depends(rate_limiter("pub_order", max_calls=20, window_seconds=60))],
)
async def place_public_order(body: _PublicOrderRequest, db: AsyncSession = DB) -> dict:
    """Buyer places an order on a public storefront."""
    # Verify merchant exists and is active — merchant_id is not trusted as auth,
    # only as a store selector. The ACTIVE check prevents ordering from suspended stores.
    m_result = await db.execute(
        select(Merchant).where(Merchant.id == body.merchant_id, Merchant.status == "ACTIVE")
    )
    if not m_result.scalar_one_or_none():
        raise NotFoundException("Store not found or is not currently active")

    order_number = f"PUB-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"

    # Validate products and compute total; raise on any invalid product
    total = 0.0
    validated_items: list[dict] = []
    for item in body.items:
        p_result = await db.execute(
            select(Product).where(
                Product.id == item.product_id,
                Product.merchant_id == body.merchant_id,  # tenant-scoped
                Product.is_published.is_(True),
            )
        )
        product = p_result.scalar_one_or_none()
        if not product:
            raise BadRequestException(
                f"Product '{item.product_id}' is not available in this store"
            )

        variant: ProductVariant | None = None
        if item.variant_id:
            v_result = await db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id,
                    ProductVariant.product_id == product.id,
                )
            )
            variant = v_result.scalar_one_or_none()
            if not variant:
                raise BadRequestException(
                    f"Variant '{item.variant_id}' not found for product '{product.name}'"
                )
            # Pre-flight stock check (non-atomic; the atomic guard is in deduct_for_order)
            if variant.stock_quantity < item.quantity:
                raise OutOfStockException(
                    f"'{product.name}' has only {variant.stock_quantity} unit(s) available, "
                    f"{item.quantity} requested"
                )
        else:
            # If the product has variants, variant_id is mandatory so stock can be
            # tracked and deducted. Sending no variant_id would silently skip deduction.
            has_variants = (
                await db.execute(
                    select(func.count())
                    .select_from(ProductVariant)
                    .where(ProductVariant.product_id == product.id)
                )
            ).scalar_one() > 0
            if has_variants:
                raise BadRequestException(
                    f"variant_id is required for '{product.name}' — "
                    "please select a product variant"
                )

        price = float(
            variant.price if variant and variant.price else product.sale_price or product.base_price
        )
        total += price * item.quantity
        validated_items.append({"product": product, "variant": variant, "qty": item.quantity, "price": price})

    # Find or create customer scoped to this merchant
    c_result = await db.execute(
        select(Customer).where(
            Customer.merchant_id == body.merchant_id,
            Customer.phone == body.customer_phone,
        )
    )
    customer = c_result.scalar_one_or_none()
    if not customer:
        customer = Customer(
            merchant_id=body.merchant_id,
            name=body.customer_name,
            phone=body.customer_phone,
            email=body.customer_email,
            address=body.delivery_address,
        )
        db.add(customer)
        await db.flush()

    try:
        payment_method = PaymentMethod(body.payment_method.upper())
    except ValueError:
        payment_method = PaymentMethod.COD

    grand_total = total + body.delivery_charge
    order = Order(
        merchant_id=body.merchant_id,
        customer_id=customer.id,
        order_number=order_number,
        status=OrderStatus.PENDING,
        channel=OrderChannel.WEBSITE,
        payment_method=payment_method,
        payment_status=PaymentStatus.UNPAID,
        subtotal=total,
        shipping_cost=body.delivery_charge,
        discount_amount=0,
        total_amount=grand_total,
        paid_amount=0,
        due_amount=grand_total,
        delivery_address=body.delivery_address,
        delivery_district=body.delivery_district or "",
        notes=body.notes or "",
    )
    db.add(order)
    await db.flush()

    for vi in validated_items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=vi["product"].id,
                variant_id=vi["variant"].id if vi["variant"] else None,
                product_name=vi["product"].name,
                variant_name=vi["variant"].name if vi["variant"] else None,
                quantity=vi["qty"],
                unit_price=vi["price"],
                total_price=vi["price"] * vi["qty"],
            )
        )
    await db.flush()

    # Atomically deduct stock for variant-tracked items under row-level lock.
    # If any item is now out of stock the exception rolls back the entire transaction.
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    await inventory_service.deduct_for_order(
        db, body.merchant_id, order.id, list(items_result.scalars().all())
    )

    # get_db commits on successful return — no explicit commit needed here.
    return {
        "success": True,
        "data": {
            "order_id": order.id,
            "order_number": order.order_number,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_method": order.payment_method,
        },
    }


@router.get(
    "/orders/{order_id}",
    dependencies=[Depends(rate_limiter("pub_order_get", max_calls=30, window_seconds=60))],
)
async def get_public_order(order_id: str, db: AsyncSession = DB) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    return {"success": True, "data": _order_detail(order)}


@router.get(
    "/track",
    dependencies=[Depends(rate_limiter("pub_track", max_calls=20, window_seconds=60))],
)
async def track_order(
    order_number: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    db: AsyncSession = DB,
) -> dict:
    """Track order by order number and/or phone number."""
    if not order_number and not phone:
        raise BadRequestException("Provide order_number or phone")

    q = select(Order)
    if order_number:
        q = q.where(Order.order_number == order_number.strip().upper())
    if phone:
        q = q.join(Customer, Order.customer_id == Customer.id).where(
            Customer.phone == phone.strip()
        )
    q = q.limit(10)

    result = await db.execute(q)
    orders = result.scalars().all()
    if not orders:
        raise NotFoundException("No orders found")

    return {"success": True, "data": {"orders": [_order_detail(o) for o in orders]}}
