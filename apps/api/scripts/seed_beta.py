"""
Beta seed — realistic demo data for SellerMate beta testing.
100 products, 20 customers, 50 orders, inventory history.

Usage:
  cd apps/api
  python -m scripts.seed_beta
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import get_settings
import app.models  # noqa: F401

from app.models.customer import Customer, CustomerSource
from app.models.inventory import InventoryChangeType, InventoryLog
from app.models.merchant import BusinessType, Merchant, MerchantRole, MerchantStatus, SubscriptionPlan
from app.models.order import Order, OrderChannel, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.models.product import Product, ProductVariant

DEMO_PHONE    = "+8801700000001"
DEMO_EMAIL    = "demo@sellermate.ai"
DEMO_PASSWORD = "Demo1234!"

rng = random.Random(42)

# ── Products ──────────────────────────────────────────────────────────────────
# (name, category, sku_prefix, base_price, sale_price, stock_qty)
PRODUCTS_DATA = [
    # Fashion Tops (15)
    ("Summer Floral Kurti",          "FASHION_TOPS", "TOP", 850,  720,  45),
    ("Embroidered Neckline Kurti",   "FASHION_TOPS", "TOP", 950,  799,  30),
    ("Plain Cotton Blouse",          "FASHION_TOPS", "TOP", 450,  380,  60),
    ("Chiffon Party Top",            "FASHION_TOPS", "TOP", 1100, 899,  20),
    ("Block Print Kurti",            "FASHION_TOPS", "TOP", 780,  650,  35),
    ("Tie-Dye Casual Kurti",         "FASHION_TOPS", "TOP", 620,  520,  50),
    ("Silk Blend Top",               "FASHION_TOPS", "TOP", 1250, 1050, 15),
    ("Stripe Cotton Shirt — Women",  "FASHION_TOPS", "TOP", 550,  460,  40),
    ("Men's Polo Shirt — Slim Fit",  "FASHION_TOPS", "TOP", 650,  550,  55),
    ("Men's Casual T-Shirt Pack 3",  "FASHION_TOPS", "TOP", 850,  720,  25),
    ("Men's Formal Dress Shirt",     "FASHION_TOPS", "TOP", 980,  820,  30),
    ("Men's Printed T-Shirt",        "FASHION_TOPS", "TOP", 420,  350,  70),
    ("Henley Neck Cotton Tee",       "FASHION_TOPS", "TOP", 480,  399,  45),
    ("Linen Summer Shirt",           "FASHION_TOPS", "TOP", 890,  740,  20),
    ("Jersey Round Neck Top",        "FASHION_TOPS", "TOP", 380,  320,   0),  # out of stock
    # Sarees (10)
    ("Printed Cotton Saree",         "FASHION_SAREE", "SAR", 1200, 980,  18),
    ("Muslin Silk Saree — Beige",    "FASHION_SAREE", "SAR", 2500, 2100,  8),
    ("Tant Saree — White & Red",     "FASHION_SAREE", "SAR", 900,  760,  22),
    ("Jamdani Saree — Traditional",  "FASHION_SAREE", "SAR", 3200, 2800,  5),
    ("Georgette Party Saree",        "FASHION_SAREE", "SAR", 1800, 1499, 12),
    ("Cotton Katan Saree",           "FASHION_SAREE", "SAR", 1400, 1150, 15),
    ("Half Silk Saree",              "FASHION_SAREE", "SAR", 1650, 1350, 10),
    ("Block Print Saree — Blue",     "FASHION_SAREE", "SAR", 1100, 900,  20),
    ("Linen Saree — Natural",        "FASHION_SAREE", "SAR", 2100, 1750,  7),
    ("Embroidered Silk Saree",       "FASHION_SAREE", "SAR", 4200, 3600,  3),
    # Ethnic (10)
    ("Embroidered Panjabi — White",  "FASHION_ETHNIC", "ETH", 1500, 1299, 25),
    ("Kurta Shalwar Set — Men",      "FASHION_ETHNIC", "ETH", 1800, 1550, 18),
    ("Eid Special Panjabi — Navy",   "FASHION_ETHNIC", "ETH", 2200, 1900, 12),
    ("Women's Salwar Kameez Set",    "FASHION_ETHNIC", "ETH", 1350, 1100, 22),
    ("Silk Panjabi — Premium",       "FASHION_ETHNIC", "ETH", 2800, 2400,  8),
    ("Cotton Punjabi — Daily",       "FASHION_ETHNIC", "ETH", 780,  650,  40),
    ("Anarkali Suit — Full Set",     "FASHION_ETHNIC", "ETH", 2500, 2100, 10),
    ("Sharara Set — Festive",        "FASHION_ETHNIC", "ETH", 2900, 2500,  6),
    ("Palazzo Set — Ladies",         "FASHION_ETHNIC", "ETH", 1200, 980,  28),
    ("Lehenga Choli — Party Wear",   "FASHION_ETHNIC", "ETH", 3500, 2999,  4),
    # Footwear (10)
    ("Ladies Sandal — Block Heel",   "FOOTWEAR", "FTW", 680,  560,  30),
    ("Men's Oxford Formal Shoe",     "FOOTWEAR", "FTW", 1500, 1250, 15),
    ("Sports Sneakers — Unisex",     "FOOTWEAR", "FTW", 1200, 999,  25),
    ("Flat Slip-On Sandal",          "FOOTWEAR", "FTW", 380,  299,  50),
    ("Leather Loafer — Men's",       "FOOTWEAR", "FTW", 1800, 1499, 12),
    ("High Heel Pumps",              "FOOTWEAR", "FTW", 1100, 899,  18),
    ("Kids School Shoe",             "FOOTWEAR", "FTW", 650,  540,  35),
    ("Rain Boot — Waterproof",       "FOOTWEAR", "FTW", 850,  699,  20),
    ("Running Shoe — Lightweight",   "FOOTWEAR", "FTW", 1400, 1150, 10),
    ("Ethnic Mojari Slipper",        "FOOTWEAR", "FTW", 450,  380,   0),  # out of stock
    # Accessories (10)
    ("Silk Dupatta — Red",           "FASHION_ACC", "ACC", 350,  299,  60),
    ("Embroidered Stole — Cream",    "FASHION_ACC", "ACC", 480,  399,  45),
    ("Women's Handbag — Tote",       "FASHION_ACC", "ACC", 950,  790,  20),
    ("Clutch Purse — Evening",       "FASHION_ACC", "ACC", 650,  540,  15),
    ("Leather Belt — Men's",         "FASHION_ACC", "ACC", 380,  299,  40),
    ("Silk Scarf — Floral",          "FASHION_ACC", "ACC", 520,  440,  30),
    ("Statement Necklace Set",       "FASHION_ACC", "ACC", 750,  620,  22),
    ("Earring Set — Gold Plated",    "FASHION_ACC", "ACC", 280,  230,  55),
    ("Hair Clip Set — Pastel",       "FASHION_ACC", "ACC", 180,  149,  80),
    ("Sunglasses — Oval Frame",      "FASHION_ACC", "ACC", 420,  349,  18),
    # Kids (10)
    ("Kids T-Shirt Pack 3pc",        "KIDS_CLOTHING", "KID", 750,  620,  35),
    ("Baby Romper Set",              "KIDS_CLOTHING", "KID", 580,  480,  28),
    ("Boy's Jeans & Shirt Combo",    "KIDS_CLOTHING", "KID", 980,  820,  20),
    ("Girl's Frock — Party",         "KIDS_CLOTHING", "KID", 850,  710,  15),
    ("Newborn Blanket Set",          "KIDS_CLOTHING", "KID", 650,  540,  40),
    ("Kids Winter Jacket",           "KIDS_CLOTHING", "KID", 1200, 999,  10),
    ("School Uniform Set — Boys",    "KIDS_CLOTHING", "KID", 780,  650,  30),
    ("School Uniform Set — Girls",   "KIDS_CLOTHING", "KID", 780,  650,  30),
    ("Cartoon Print Pyjama Set",     "KIDS_CLOTHING", "KID", 480,  399,  45),
    ("Baby Booties & Cap Set",       "KIDS_CLOTHING", "KID", 320,  265,  50),
    # Bottoms (5)
    ("Denim Jeans — Slim Fit",       "FASHION_BOTTOMS", "BOT", 1100, 899,  25),
    ("Palazzo Pants — Casual",       "FASHION_BOTTOMS", "BOT", 580,  480,  35),
    ("Jogger Pants — Unisex",        "FASHION_BOTTOMS", "BOT", 650,  540,  40),
    ("Chino Trousers — Men's",       "FASHION_BOTTOMS", "BOT", 890,  740,  20),
    ("Maxi Skirt — Floral",          "FASHION_BOTTOMS", "BOT", 720,  599,  18),
    # Beauty (10)
    ("Rose Water Face Mist 150ml",   "BEAUTY", "BTY", 280,  230,  70),
    ("Herbal Hair Oil 200ml",        "BEAUTY", "BTY", 350,  299,  55),
    ("Natural Face Wash — Neem",     "BEAUTY", "BTY", 220,  180,  80),
    ("Kojic Acid Face Cream 50g",    "BEAUTY", "BTY", 480,  399,  40),
    ("Charcoal Face Mask 100g",      "BEAUTY", "BTY", 320,  265,  45),
    ("Vitamin C Serum 30ml",         "BEAUTY", "BTY", 650,  540,  30),
    ("Collagen Under-Eye Patches",   "BEAUTY", "BTY", 280,  230,  60),
    ("Natural Lip Balm Set 3pc",     "BEAUTY", "BTY", 180,  149,  90),
    ("Aloe Vera Gel 250ml",          "BEAUTY", "BTY", 220,  180,  70),
    ("Body Lotion — Lightening",     "BEAUTY", "BTY", 380,  315,  50),
    # Home (10)
    ("Cotton Bedsheet Set — King",   "HOME_DECOR", "HOM", 1800, 1499, 12),
    ("Decorative Throw Pillow 2pc",  "HOME_DECOR", "HOM", 580,  480,  20),
    ("Ceramic Flower Vase",          "HOME_DECOR", "HOM", 420,  349,  15),
    ("Scented Candle Set 3pc",       "HOME_DECOR", "HOM", 480,  399,  25),
    ("Bamboo Storage Basket",        "HOME_DECOR", "HOM", 650,  540,  18),
    ("Wall Art Print — Bengali",     "HOME_DECOR", "HOM", 380,  315,  22),
    ("Photo Frame Set — Wooden",     "HOME_DECOR", "HOM", 520,  440,  20),
    ("Dinner Set — 24 Pieces",       "HOME_DECOR", "HOM", 2200, 1850,  8),
    ("Kitchen Knife Set",            "HOME_DECOR", "HOM", 980,  820,  10),
    ("Muslin Curtain Pair",          "HOME_DECOR", "HOM", 850,  710,  14),
]

CUSTOMERS_DATA = [
    ("Fatima Begum",     "+8801711111111", "fatima@gmail.com",   "Dhaka",       CustomerSource.FACEBOOK),
    ("Rahela Khatun",    "+8801722222222", None,                 "Chittagong",  CustomerSource.WHATSAPP),
    ("Sadia Islam",      "+8801733333333", "sadia@yahoo.com",    "Sylhet",      CustomerSource.MANUAL),
    ("Tahmina Akter",    "+8801744444444", None,                 "Rajshahi",    CustomerSource.FACEBOOK),
    ("Nasrin Jahan",     "+8801755555555", "nasrin@gmail.com",   "Dhaka",       CustomerSource.INSTAGRAM),
    ("Roksana Parvin",   "+8801766666666", None,                 "Khulna",      CustomerSource.WHATSAPP),
    ("Sumaiya Khanam",   "+8801777777777", "sumaiya@gmail.com",  "Dhaka",       CustomerSource.FACEBOOK),
    ("Maliha Ahmed",     "+8801788888888", None,                 "Comilla",     CustomerSource.INSTAGRAM),
    ("Jesmin Akter",     "+8801799999999", "jesmin@outlook.com", "Bogura",      CustomerSource.FACEBOOK),
    ("Nipa Sultana",     "+8801811111111", None,                 "Mymensingh",  CustomerSource.WHATSAPP),
    ("Sharmin Nahar",    "+8801822222222", "sharmin@gmail.com",  "Dhaka",       CustomerSource.MANUAL),
    ("Parveen Hossain",  "+8801833333333", None,                 "Narayanganj", CustomerSource.FACEBOOK),
    ("Rumi Begum",       "+8801844444444", "rumi@yahoo.com",     "Dhaka",       CustomerSource.INSTAGRAM),
    ("Tania Akter",      "+8801855555555", None,                 "Gazipur",     CustomerSource.WHATSAPP),
    ("Mim Islam",        "+8801866666666", "mim@gmail.com",      "Dhaka",       CustomerSource.FACEBOOK),
    ("Anika Rahman",     "+8801877777777", None,                 "Sylhet",      CustomerSource.INSTAGRAM),
    ("Sabrina Afrin",    "+8801888888888", "sabrina@gmail.com",  "Chittagong",  CustomerSource.MANUAL),
    ("Nusrat Jahan",     "+8801899999999", None,                 "Dhaka",       CustomerSource.FACEBOOK),
    ("Reshma Khatun",    "+8801911111111", "reshma@outlook.com", "Rajshahi",    CustomerSource.WHATSAPP),
    ("Dilnoza Begum",    "+8801922222222", None,                 "Dhaka",       CustomerSource.FACEBOOK),
]


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # ── Merchant ──────────────────────────────────────────────────────────
        result = await db.execute(select(Merchant).where(Merchant.phone == DEMO_PHONE))
        merchant = result.scalar_one_or_none()

        if not merchant:
            pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
            merchant = Merchant(
                email=DEMO_EMAIL,
                phone=DEMO_PHONE,
                password_hash=pw_hash,
                business_name="Fresh Test Shop",
                owner_name="Demo Owner",
                business_type=BusinessType.FASHION_CLOTHING,
                district="Dhaka",
                division="Dhaka",
                address="House 12, Road 5, Dhanmondi, Dhaka",
                trust_score=85,
                status=MerchantStatus.ACTIVE,
                plan=SubscriptionPlan.PRO,
                onboarding_done=True,
                role=MerchantRole.OWNER,
                store_slug="demo-shop",
                store_description="Bangladesh's most loved fashion store — quality at affordable prices.",
                whatsapp_phone=DEMO_PHONE,
            )
            db.add(merchant)
            await db.flush()
            print(f"[ok] Created demo merchant {merchant.id}")
        else:
            # Move the demo email off any stale merchant that is NOT the demo-shop merchant
            dup = (await db.execute(
                select(Merchant).where(Merchant.email == DEMO_EMAIL, Merchant.id != merchant.id)
            )).scalar_one_or_none()
            if dup:
                dup.email = f"stale_{dup.id[:8]}@example.com"
                await db.flush()
                print(f"[clean] Reassigned email on stale merchant {dup.id}")

            # Always sync demo credentials and key fields
            pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
            merchant.email = DEMO_EMAIL
            merchant.password_hash = pw_hash
            merchant.store_slug = "demo-shop"
            merchant.store_description = "Bangladesh's most loved fashion store — quality at affordable prices."
            merchant.whatsapp_phone = DEMO_PHONE
            merchant.status = MerchantStatus.ACTIVE
            merchant.onboarding_done = True
            merchant.district = "Dhaka"
            print(f"[update] Merchant credentials synced: {merchant.id}")

        mid = merchant.id

        # ── Products ──────────────────────────────────────────────────────────
        existing_prods = (
            await db.execute(select(Product).where(Product.merchant_id == mid))
        ).scalars().all()

        if len(existing_prods) >= 90:
            print(f"[skip] {len(existing_prods)} products already seeded")
            products = list(existing_prods)
        else:
            # Must delete orders & their items first (FK dependency)
            existing_ords_early = (
                await db.execute(select(Order).where(Order.merchant_id == mid))
            ).scalars().all()
            for o in existing_ords_early:
                await db.delete(o)
            await db.flush()

            # Now safe to delete products
            for p in existing_prods:
                await db.delete(p)
            await db.flush()

            products: list[Product] = []
            for idx, (name, cat, sku_pfx, base, sale, stock) in enumerate(PRODUCTS_DATA, 1):
                sku = f"{sku_pfx}-{idx:03d}"
                prod = Product(
                    merchant_id=mid,
                    name=name,
                    category=cat,
                    sku=sku,
                    base_price=Decimal(str(base)),
                    sale_price=Decimal(str(sale)),
                    is_active=True,
                    is_published=True,
                    total_sold=rng.randint(0, 30),
                )
                db.add(prod)
                products.append(prod)
            await db.flush()

            # Add default variant for each product
            for prod, (_, _, _, _, _, stock) in zip(products, PRODUCTS_DATA):
                variant = ProductVariant(
                    product_id=prod.id,
                    name="Default",
                    sku=f"{prod.sku}-DEF",
                    stock_quantity=stock,
                    low_stock_alert=5,
                )
                db.add(variant)
            await db.flush()
            print(f"[ok] Created {len(products)} products with variants")

        # ── Customers ─────────────────────────────────────────────────────────
        existing_custs = (
            await db.execute(select(Customer).where(Customer.merchant_id == mid))
        ).scalars().all()

        if len(existing_custs) >= 18:
            print(f"[skip] {len(existing_custs)} customers already seeded")
            customers = list(existing_custs)
        else:
            for c in existing_custs:
                await db.delete(c)
            await db.flush()

            customers: list[Customer] = []
            for name, phone, email, district, source in CUSTOMERS_DATA:
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
                db.add(c)
                customers.append(c)
            await db.flush()
            print(f"[ok] Created {len(customers)} customers")

        # ── Orders ────────────────────────────────────────────────────────────
        existing_orders = (
            await db.execute(select(Order).where(Order.merchant_id == mid))
        ).scalars().all()

        if len(existing_orders) >= 40:
            print(f"[skip] {len(existing_orders)} orders already seeded")
        else:
            # Delete any remaining (may have been cleared above with products)
            for o in existing_orders:
                await db.delete(o)
            await db.flush()

            # Reset customer counters
            for c in customers:
                c.total_orders = 0
                c.total_spent = Decimal("0")

            now_utc = datetime.now(timezone.utc)

            # Order spec: (customer_idx, product_idx, qty, status, payment_status, days_ago)
            ORDER_SPECS = [
                (0,  0,  2, OrderStatus.DELIVERED,  PaymentStatus.PAID,    28),
                (1,  15, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,    25),
                (2,  2,  3, OrderStatus.DELIVERED,  PaymentStatus.PAID,    22),
                (3,  25, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,    20),
                (4,  50, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,    18),
                (5,  60, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,    17),
                (6,  10, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,    15),
                (7,  35, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,    14),
                (8,  80, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,    12),
                (9,  5,  1, OrderStatus.DELIVERED,  PaymentStatus.PAID,    10),
                (10, 20, 1, OrderStatus.SHIPPED,    PaymentStatus.UNPAID,   7),
                (11, 30, 2, OrderStatus.SHIPPED,    PaymentStatus.PAID,     6),
                (12, 1,  1, OrderStatus.SHIPPED,    PaymentStatus.UNPAID,   5),
                (13, 45, 3, OrderStatus.SHIPPED,    PaymentStatus.PAID,     4),
                (14, 65, 1, OrderStatus.SHIPPED,    PaymentStatus.UNPAID,   3),
                (15, 71, 2, OrderStatus.PROCESSING, PaymentStatus.PAID,     3),
                (16, 55, 1, OrderStatus.PROCESSING, PaymentStatus.UNPAID,   2),
                (17, 12, 2, OrderStatus.PROCESSING, PaymentStatus.PAID,     2),
                (18, 40, 1, OrderStatus.PROCESSING, PaymentStatus.UNPAID,   1),
                (19, 90, 1, OrderStatus.PROCESSING, PaymentStatus.PAID,     1),
                (0,  3,  1, OrderStatus.CONFIRMED,  PaymentStatus.UNPAID,   1),
                (1,  18, 2, OrderStatus.CONFIRMED,  PaymentStatus.PAID,     1),
                (2,  28, 1, OrderStatus.CONFIRMED,  PaymentStatus.UNPAID,   0),
                (3,  48, 1, OrderStatus.CONFIRMED,  PaymentStatus.PAID,     0),
                (4,  58, 2, OrderStatus.CONFIRMED,  PaymentStatus.UNPAID,   0),
                (5,  7,  1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (6,  22, 1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (7,  37, 2, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (8,  52, 1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (9,  68, 1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (10, 75, 1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (11, 85, 2, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (12, 95, 1, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (13, 4,  1, OrderStatus.CANCELLED,  PaymentStatus.UNPAID,   9),
                (14, 14, 1, OrderStatus.CANCELLED,  PaymentStatus.UNPAID,   11),
                (15, 24, 2, OrderStatus.CANCELLED,  PaymentStatus.UNPAID,   13),
                (16, 34, 1, OrderStatus.CANCELLED,  PaymentStatus.UNPAID,   16),
                (0,  6,  1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     30),
                (1,  16, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,     29),
                (2,  26, 1, OrderStatus.SHIPPED,    PaymentStatus.PAID,     5),
                (3,  36, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     19),
                (4,  46, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,     21),
                (5,  56, 1, OrderStatus.PROCESSING, PaymentStatus.UNPAID,   2),
                (6,  66, 1, OrderStatus.CONFIRMED,  PaymentStatus.PAID,     1),
                (7,  76, 2, OrderStatus.DELIVERED,  PaymentStatus.PAID,     23),
                (8,  86, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     24),
                (9,  96, 1, OrderStatus.SHIPPED,    PaymentStatus.UNPAID,   4),
                (10, 9,  1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     26),
                (11, 19, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     27),
                (12, 29, 2, OrderStatus.PENDING,    PaymentStatus.UNPAID,   0),
                (13, 39, 1, OrderStatus.DELIVERED,  PaymentStatus.PAID,     15),
            ]

            CHANNELS = [
                OrderChannel.FACEBOOK, OrderChannel.WHATSAPP,
                OrderChannel.INSTAGRAM, OrderChannel.WEBSITE, OrderChannel.MANUAL,
            ]
            METHODS = [
                PaymentMethod.BKASH, PaymentMethod.COD,
                PaymentMethod.NAGAD, PaymentMethod.BKASH,
            ]

            created_orders = 0
            for idx, (cidx, pidx, qty, ostatus, pstatus, days_ago) in enumerate(ORDER_SPECS, 1):
                cust = customers[cidx % len(customers)]
                prod = products[pidx % len(products)]

                unit_price = prod.sale_price or prod.base_price
                subtotal   = unit_price * qty
                shipping   = Decimal("60")
                total      = subtotal + shipping
                paid       = (total if pstatus == PaymentStatus.PAID
                              else total / 2 if pstatus == PaymentStatus.PARTIAL
                              else Decimal("0"))

                created_at = now_utc - timedelta(days=days_ago, hours=rng.randint(0, 23))

                order = Order(
                    merchant_id=mid,
                    customer_id=cust.id,
                    order_number=f"SM-BETA-{idx:04d}",
                    status=ostatus,
                    channel=rng.choice(CHANNELS),
                    subtotal=subtotal,
                    discount_amount=Decimal("0"),
                    shipping_cost=shipping,
                    total_amount=total,
                    paid_amount=paid,
                    due_amount=total - paid,
                    payment_method=rng.choice(METHODS),
                    payment_status=pstatus,
                    delivery_address=f"{cust.name}, {cust.district}",
                    delivery_district=cust.district,
                    notes="Beta demo order",
                )
                order.created_at = created_at  # type: ignore[assignment]
                db.add(order)
                await db.flush()

                db.add(OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=unit_price * qty,
                ))

                cust.total_orders += 1
                cust.total_spent  += total
                created_orders    += 1

            await db.flush()
            print(f"[ok] Created {created_orders} orders")

        await db.commit()

    await engine.dispose()
    print("\nBeta seed complete.")
    print(f"  Phone: {DEMO_PHONE}  /  Email: {DEMO_EMAIL}  /  Password: {DEMO_PASSWORD}")
    print(f"  Store: http://localhost:3000/store/demo-shop")


if __name__ == "__main__":
    asyncio.run(seed())
