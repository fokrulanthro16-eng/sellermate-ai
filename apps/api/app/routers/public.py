"""Public (unauthenticated) storefront and marketplace endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.order import Order, OrderChannel, OrderStatus, PaymentMethod, PaymentStatus
from app.models.order import OrderItem
from app.models.product import Product

router = APIRouter()
DB = Depends(get_db)


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

    # Batch fetch product counts
    counts: dict = {}
    if merchants:
        ids = [m.id for m in merchants]
        count_q = select(Product.merchant_id, func.count().label("cnt")).where(
            Product.merchant_id.in_(ids), Product.is_published.is_(True)
        ).group_by(Product.merchant_id)
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


@router.get("/search")
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
        stmt = stmt.where(or_(
            Product.name.ilike(f"%{q}%"),
            Product.name_bangla.ilike(f"%{q}%"),
            Product.description.ilike(f"%{q}%"),
        ))
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
    # Haversine approximation via bounding box filter
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * abs(__import__("math").cos(__import__("math").radians(lat))) or 1)
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


@router.post("/orders")
async def place_public_order(body: dict, db: AsyncSession = DB) -> dict:
    """Buyer places an order on a public storefront."""
    merchant_id = body.get("merchant_id", "")
    items = body.get("items", [])
    if not merchant_id or not items:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("merchant_id and items are required")

    # Verify merchant exists
    m_result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    if not m_result.scalar_one_or_none():
        raise NotFoundException("Merchant not found")

    # Build order number
    import time as _time
    order_number = f"PUB-{int(_time.time())}-{uuid.uuid4().hex[:4].upper()}"

    # Calculate total from DB prices
    total = 0.0
    validated_items = []
    for item in items:
        pid = item.get("product_id", "")
        qty = int(item.get("quantity", 1))
        p_result = await db.execute(
            select(Product).where(Product.id == pid, Product.merchant_id == merchant_id, Product.is_published.is_(True))
        )
        product = p_result.scalar_one_or_none()
        if not product:
            continue
        price = float(product.sale_price or product.base_price)
        total += price * qty
        validated_items.append({"product": product, "qty": qty, "price": price})

    if not validated_items:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("No valid published products in order")

    # Create a stub customer record or find existing
    from app.models.customer import Customer
    cust_phone = body.get("customer_phone", "")
    cust_name = body.get("customer_name", "Buyer")
    c_result = await db.execute(
        select(Customer).where(Customer.merchant_id == merchant_id, Customer.phone == cust_phone)
    )
    customer = c_result.scalar_one_or_none()
    if not customer:
        customer = Customer(
            merchant_id=merchant_id,
            name=cust_name,
            phone=cust_phone,
            email=body.get("customer_email"),
            address=body.get("delivery_address"),
        )
        db.add(customer)
        await db.flush()

    payment_method_str = (body.get("payment_method") or "COD").upper()
    try:
        payment_method = PaymentMethod(payment_method_str)
    except ValueError:
        payment_method = PaymentMethod.COD

    shipping = float(body.get("delivery_charge", 60))
    grand_total = total + shipping
    order = Order(
        merchant_id=merchant_id,
        customer_id=customer.id,
        order_number=order_number,
        status=OrderStatus.PENDING,
        channel=OrderChannel.WEBSITE,
        payment_method=payment_method,
        payment_status=PaymentStatus.UNPAID,
        subtotal=total,
        shipping_cost=shipping,
        discount_amount=0,
        total_amount=grand_total,
        paid_amount=0,
        due_amount=grand_total,
        delivery_address=body.get("delivery_address", ""),
        delivery_district=body.get("delivery_district", ""),
        notes=body.get("notes", ""),
    )
    db.add(order)
    await db.flush()

    for vi in validated_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=vi["product"].id,
            product_name=vi["product"].name,
            quantity=vi["qty"],
            unit_price=vi["price"],
            total_price=vi["price"] * vi["qty"],
        ))

    await db.commit()
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


@router.get("/orders/{order_id}")
async def get_public_order(order_id: str, db: AsyncSession = DB) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    return {
        "success": True,
        "data": _order_detail(order),
    }


@router.get("/track")
async def track_order(
    order_number: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    db: AsyncSession = DB,
) -> dict:
    """Track order by order number and/or phone number."""
    if not order_number and not phone:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Provide order_number or phone")

    q = select(Order)
    if order_number:
        q = q.where(Order.order_number == order_number.strip().upper())
    if phone:
        from app.models.customer import Customer
        # join through customer to match phone
        phone_clean = phone.strip()
        q = q.join(Customer, Order.customer_id == Customer.id).where(Customer.phone == phone_clean)
    q = q.limit(10)

    result = await db.execute(q)
    orders = result.scalars().all()
    if not orders:
        raise NotFoundException("No orders found")

    return {
        "success": True,
        "data": {"orders": [_order_detail(o) for o in orders]},
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
