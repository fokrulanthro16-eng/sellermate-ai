"""Seed the database with a demo merchant, products, customers, and orders.

Usage:
  cd apps/api
  python -m scripts.seed_demo
"""
from __future__ import annotations

import asyncio
import sys
import os
from decimal import Decimal

import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Make sure app package is importable from the api root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import get_settings
import app.models  # noqa: F401 — registers all ORM models with Base

from app.models.merchant import Merchant, BusinessType, MerchantRole, MerchantStatus, SubscriptionPlan
from app.models.product import Product
from app.models.customer import Customer, CustomerSource
from app.models.order import (
    Order, OrderItem, OrderStatus, OrderChannel, PaymentMethod, PaymentStatus,
)

DEMO_PHONE = "+8801700000001"
DEMO_EMAIL = "demo@sellermate.ai"
DEMO_PASSWORD = "Demo1234!"


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── Merchant ──────────────────────────────────────────────────────────
        result = await session.execute(select(Merchant).where(Merchant.phone == DEMO_PHONE))
        merchant = result.scalar_one_or_none()

        if merchant:
            print(f"[skip] Demo merchant already exists: {merchant.id}")
        else:
            pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
            merchant = Merchant(
                email=DEMO_EMAIL,
                phone=DEMO_PHONE,
                password_hash=pw_hash,
                business_name="SellerMate Demo Store",
                owner_name="Demo Owner",
                business_type=BusinessType.FASHION_CLOTHING,
                district="Dhaka",
                division="Dhaka",
                trust_score=85,
                status=MerchantStatus.ACTIVE,
                plan=SubscriptionPlan.PRO,
                onboarding_done=True,
                role=MerchantRole.OWNER,
            )
            session.add(merchant)
            await session.flush()
            print(f"[ok] Created demo merchant {merchant.id}")

        mid = merchant.id

        # ── Products ──────────────────────────────────────────────────────────
        p_result = await session.execute(select(Product).where(Product.merchant_id == mid))
        if p_result.scalars().first():
            print("[skip] Products already seeded")
        else:
            products_data = [
                ("Summer Floral Kurti",     "FASHION_TOPS",    "SKU-001", Decimal("850"),  Decimal("720")),
                ("Printed Cotton Saree",    "FASHION_SAREE",   "SKU-002", Decimal("1200"), Decimal("980")),
                ("Men's Polo Shirt",        "FASHION_TOPS",    "SKU-003", Decimal("650"),  Decimal("550")),
                ("Ladies Sandal — Size 6",  "FOOTWEAR",        "SKU-004", Decimal("480"),  Decimal("399")),
                ("Embroidered Panjabi",     "FASHION_ETHNIC",  "SKU-005", Decimal("1500"), Decimal("1299")),
                ("Silk Dupatta — Red",      "FASHION_ACC",     "SKU-006", Decimal("350"),  Decimal("299")),
                ("Kids T-Shirt Pack (3pc)", "KIDS_CLOTHING",   "SKU-007", Decimal("750"),  Decimal("620")),
                ("Denim Jeans — Slim Fit",  "FASHION_BOTTOMS", "SKU-008", Decimal("1100"), Decimal("899")),
            ]
            products: list[Product] = []
            for name, cat, sku, base, sale in products_data:
                p = Product(
                    merchant_id=mid,
                    name=name,
                    category=cat,
                    sku=sku,
                    base_price=base,
                    sale_price=sale,
                    is_active=True,
                    is_published=True,
                )
                session.add(p)
                products.append(p)
            await session.flush()
            print(f"[ok] Created {len(products)} products")

        # ── Customers ─────────────────────────────────────────────────────────
        c_result = await session.execute(select(Customer).where(Customer.merchant_id == mid))
        existing_customers = c_result.scalars().all()

        if existing_customers:
            print("[skip] Customers already seeded")
            customers: list[Customer] = list(existing_customers)
        else:
            customers_data = [
                ("Fatima Begum",   "+8801711111111", "fatima@gmail.com", "Dhaka",     CustomerSource.FACEBOOK),
                ("Rahela Khatun",  "+8801722222222", None,               "Chittagong",CustomerSource.WHATSAPP),
                ("Sadia Islam",    "+8801733333333", "sadia@yahoo.com",  "Sylhet",    CustomerSource.MANUAL),
                ("Tahmina Akter",  "+8801744444444", None,               "Rajshahi",  CustomerSource.FACEBOOK),
                ("Nasrin Jahan",   "+8801755555555", "nasrin@gmail.com", "Dhaka",     CustomerSource.INSTAGRAM),
            ]
            customers = []
            for name, phone, email, district, source in customers_data:
                c = Customer(
                    merchant_id=mid,
                    name=name,
                    phone=phone,
                    email=email,
                    district=district,
                    source=source,
                    total_orders=0,
                    total_spent=Decimal("0"),
                )
                session.add(c)
                customers.append(c)
            await session.flush()
            print(f"[ok] Created {len(customers)} customers")

        # ── Orders ────────────────────────────────────────────────────────────
        o_result = await session.execute(select(Order).where(Order.merchant_id == mid))
        if o_result.scalars().first():
            print("[skip] Orders already seeded")
        else:
            all_products = (
                await session.execute(select(Product).where(Product.merchant_id == mid))
            ).scalars().all()

            orders_spec = [
                (customers[0], all_products[0], 2, OrderStatus.DELIVERED,  PaymentStatus.PAID),
                (customers[1], all_products[1], 1, OrderStatus.SHIPPED,    PaymentStatus.UNPAID),
                (customers[2], all_products[2], 3, OrderStatus.CONFIRMED,  PaymentStatus.PAID),
                (customers[0], all_products[3], 1, OrderStatus.PENDING,    PaymentStatus.UNPAID),
                (customers[3], all_products[4], 2, OrderStatus.PROCESSING, PaymentStatus.PARTIAL),
                (customers[4], all_products[5], 1, OrderStatus.DELIVERED,  PaymentStatus.PAID),
            ]

            for idx, (cust, prod, qty, ostatus, pstatus) in enumerate(orders_spec, 1):
                unit_price = prod.sale_price or prod.base_price
                subtotal = unit_price * qty
                shipping = Decimal("60")
                total = subtotal + shipping
                if pstatus == PaymentStatus.PAID:
                    paid = total
                elif pstatus == PaymentStatus.PARTIAL:
                    paid = total / 2
                else:
                    paid = Decimal("0")

                order = Order(
                    merchant_id=mid,
                    customer_id=cust.id,
                    order_number=f"SM-DEMO-{idx:04d}",
                    status=ostatus,
                    channel=OrderChannel.FACEBOOK,
                    subtotal=subtotal,
                    discount_amount=Decimal("0"),
                    shipping_cost=shipping,
                    total_amount=total,
                    paid_amount=paid,
                    due_amount=total - paid,
                    payment_method=PaymentMethod.BKASH,
                    payment_status=pstatus,
                    delivery_address=f"{cust.name}, {cust.district}",
                    delivery_district=cust.district,
                    notes="Demo order",
                )
                session.add(order)
                await session.flush()

                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=unit_price * qty,
                )
                session.add(item)

                cust.total_orders += 1
                cust.total_spent += total

            await session.flush()
            print(f"[ok] Created {len(orders_spec)} orders")

        await session.commit()

    await engine.dispose()
    print("\nSeed complete.")
    print(f"  Demo login  phone: {DEMO_PHONE}  /  email: {DEMO_EMAIL}  /  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
