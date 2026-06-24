#!/usr/bin/env python3
"""
SellerMate AI — Demo Data Seeder v2
Creates realistic Bangladeshi e-commerce data for the demo merchant.
Target: 30 products, 60+ variants, 100 customers, 180 orders.
Run: python seed_demo_data.py
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import asyncpg

DB_URL = "postgresql://sellermate:sellermate123@localhost:5432/sellermate"
DEMO_EMAIL = "demo@sellermate.ai"

random.seed(42)

# ── Bangladeshi Data ────────────────────────────────────────────────────────────

BD_NAMES = [
    "রাহেলা বেগম", "করিম উদ্দিন", "সুমাইয়া খানম", "মোঃ আলী হাসান", "নাসরিন আক্তার",
    "রফিকুল ইসলাম", "শিরিন আক্তার", "মাহমুদুল হক", "ফাতেমা তুজ জোহরা", "আবুল কাসেম",
    "রোকেয়া সুলতানা", "নাজমুল হুদা", "সালমা বেগম", "তানভীর আহমেদ", "মরিয়ম বেগম",
    "শাহেদুল ইসলাম", "ফেরদৌসি আক্তার", "মিজানুর রহমান", "বিলকিস বানু", "আনোয়ার হোসেন",
    "নুরজাহান বেগম", "ইব্রাহিম খলিল", "সাবিনা ইয়াসমিন", "মোঃ জহিরুল ইসলাম", "হাসিনা আক্তার",
    "আবদুল মান্নান", "কামরুন নাহার", "শফিকুল আলম", "পারভীন সুলতানা", "জাকির হোসেন",
    "রাবেয়া বেগম", "মোঃ সাইফুল ইসলাম", "আয়েশা সিদ্দিকা", "নূরুল ইসলাম", "সুফিয়া বেগম",
    "মাহবুবুর রহমান", "নাছিমা আক্তার", "গোলাম মোস্তফা", "মাহফুজা বেগম", "আব্দুল্লাহ আল মামুন",
    "দিলরুবা আক্তার", "মোঃ হারুনুর রশিদ", "লাইলা আক্তার", "আতিকুর রহমান", "সুমি আক্তার",
    "মোঃ মোজাম্মেল হক", "রুমা বেগম", "শামসুল আলম", "তাহমিনা বেগম", "আমিনুল ইসলাম",
    "রেহানা পারভীন", "মোঃ ইকবাল হোসেন", "সেলিনা বেগম", "আব্দুর রহিম", "নাজমা বেগম",
    "মোঃ শহীদুল ইসলাম", "রওশন আরা", "কাজী আনোয়ার হোসেন", "আমেনা বেগম", "মোঃ মনিরুজ্জামান",
    "ফরিদা ইয়াসমিন", "মোঃ মাসুদুর রহমান", "শাহনাজ পারভীন", "রহিমুদ্দিন", "তাসলিমা বেগম",
    "মোঃ মোস্তাফিজুর রহমান", "মাহমুদা খানম", "জয়নাল আবেদীন", "শামসুন্নাহার", "মোঃ ফারুক হোসেন",
    "খুরশিদা বেগম", "মোঃ বশির আহমেদ", "জাহানারা বেগম", "আতাউর রহমান", "সখিনা বেগম",
    "মোঃ আব্দুর রাজ্জাক", "শামীমা আক্তার", "মোঃ নুরুল আলম", "বেগম রোকেয়া", "ছাদেক হোসেন",
]

BD_DISTRICTS = [
    "ঢাকা", "চট্টগ্রাম", "সিলেট", "রাজশাহী", "খুলনা", "বরিশাল", "ময়মনসিংহ", "রংপুর",
    "গাজীপুর", "নারায়ণগঞ্জ", "কুমিল্লা", "ফেনী", "নোয়াখালী", "লক্ষ্মীপুর", "চাঁদপুর",
    "ব্রাহ্মণবাড়িয়া", "কিশোরগঞ্জ", "নেত্রকোনা", "টাঙ্গাইল", "ফরিদপুর", "গোপালগঞ্জ",
    "মাদারীপুর", "শরীয়তপুর", "নরসিংদী", "মুন্সীগঞ্জ", "মানিকগঞ্জ", "রাজবাড়ী",
    "বগুড়া", "নাটোর", "সিরাজগঞ্জ", "পাবনা", "জয়পুরহাট", "চাঁপাইনবাবগঞ্জ", "নওগাঁ",
    "যশোর", "ঝিনাইদহ", "মাগুরা", "নড়াইল", "সাতক্ষীরা", "বাগেরহাট", "মেহেরপুর", "কুষ্টিয়া",
    "পিরোজপুর", "ভোলা", "ঝালকাঠি", "পটুয়াখালী", "বরগুনা", "সুনামগঞ্জ", "মৌলভীবাজার",
    "হবিগঞ্জ", "জামালপুর", "শেরপুর", "পঞ্চগড়", "ঠাকুরগাঁও", "দিনাজপুর", "নীলফামারী",
    "কুড়িগ্রাম", "লালমনিরহাট", "গাইবান্ধা", "বান্দরবান", "রাঙ্গামাটি", "খাগড়াছড়ি",
]

BD_DIVISIONS = {
    "ঢাকা": "ঢাকা", "চট্টগ্রাম": "চট্টগ্রাম", "সিলেট": "সিলেট", "রাজশাহী": "রাজশাহী",
    "খুলনা": "খুলনা", "বরিশাল": "বরিশাল", "ময়মনসিংহ": "ময়মনসিংহ", "রংপুর": "রংপুর",
    "গাজীপুর": "ঢাকা", "নারায়ণগঞ্জ": "ঢাকা", "কুমিল্লা": "চট্টগ্রাম", "ফেনী": "চট্টগ্রাম",
    "নোয়াখালী": "চট্টগ্রাম", "লক্ষ্মীপুর": "চট্টগ্রাম", "চাঁদপুর": "চট্টগ্রাম",
    "ব্রাহ্মণবাড়িয়া": "চট্টগ্রাম", "কিশোরগঞ্জ": "ঢাকা", "নেত্রকোনা": "ময়মনসিংহ",
    "টাঙ্গাইল": "ঢাকা", "ফরিদপুর": "ঢাকা", "গোপালগঞ্জ": "ঢাকা", "মাদারীপুর": "ঢাকা",
    "শরীয়তপুর": "ঢাকা", "নরসিংদী": "ঢাকা", "মুন্সীগঞ্জ": "ঢাকা", "মানিকগঞ্জ": "ঢাকা",
    "রাজবাড়ী": "ঢাকা", "বগুড়া": "রাজশাহী", "নাটোর": "রাজশাহী", "সিরাজগঞ্জ": "রাজশাহী",
    "পাবনা": "রাজশাহী", "জয়পুরহাট": "রাজশাহী", "চাঁপাইনবাবগঞ্জ": "রাজশাহী",
    "নওগাঁ": "রাজশাহী", "যশোর": "খুলনা", "ঝিনাইদহ": "খুলনা", "মাগুরা": "খুলনা",
    "নড়াইল": "খুলনা", "সাতক্ষীরা": "খুলনা", "বাগেরহাট": "খুলনা", "মেহেরপুর": "খুলনা",
    "কুষ্টিয়া": "খুলনা", "পিরোজপুর": "বরিশাল", "ভোলা": "বরিশাল", "ঝালকাঠি": "বরিশাল",
    "পটুয়াখালী": "বরিশাল", "বরগুনা": "বরিশাল", "সুনামগঞ্জ": "সিলেট",
    "মৌলভীবাজার": "সিলেট", "হবিগঞ্জ": "সিলেট", "জামালপুর": "ময়মনসিংহ",
    "শেরপুর": "ময়মনসিংহ", "পঞ্চগড়": "রংপুর", "ঠাকুরগাঁও": "রংপুর",
    "দিনাজপুর": "রংপুর", "নীলফামারী": "রংপুর", "কুড়িগ্রাম": "রংপুর",
    "লালমনিরহাট": "রংপুর", "গাইবান্ধা": "রংপুর", "বান্দরবান": "চট্টগ্রাম",
    "রাঙ্গামাটি": "চট্টগ্রাম", "খাগড়াছড়ি": "চট্টগ্রাম",
}

# ── Product Catalog ──────────────────────────────────────────────────────────────

PRODUCT_CATALOG = [
    # (name, category, base_price, variants: [(name, sku_suffix, price, stock, low_alert)])
    ("Cotton Salwar Kameez Set", "পোশাক", 850, [
        ("S - কালো", "S-BLK", 850, 25, 5),
        ("M - নীল", "M-BLU", 850, 18, 5),
        ("L - লাল", "L-RED", 900, 8, 5),
    ]),
    ("Premium Georgette Saree", "পোশাক", 1500, [
        ("লাল-সোনালি", "RED-GLD", 1500, 12, 3),
        ("সবুজ-সিলভার", "GRN-SLV", 1600, 6, 3),
    ]),
    ("Ladies Kurti Block Print", "পোশাক", 550, [
        ("S", "KRT-S", 550, 30, 8),
        ("M", "KRT-M", 550, 22, 8),
        ("XL", "KRT-XL", 600, 4, 5),
    ]),
    ("Men's Panjabi Eid Collection", "পোশাক", 1200, [
        ("M - সাদা", "PNJ-M-WHT", 1200, 15, 5),
        ("L - নীল", "PNJ-L-BLU", 1200, 10, 5),
    ]),
    ("Denim Jeans Slim Fit", "পোশাক", 950, [
        ("30\" - কালো", "JNS-30-BLK", 950, 20, 5),
        ("32\" - নীল", "JNS-32-BLU", 950, 15, 5),
        ("34\" - গ্রে", "JNS-34-GRY", 1000, 3, 5),
    ]),
    ("Leather Sandal Women", "জুতা", 650, [
        ("৩৭", "SDL-37", 650, 18, 5),
        ("৩৮", "SDL-38", 650, 25, 5),
        ("৩৯", "SDL-39", 650, 0, 5),
    ]),
    ("Sneakers Men White", "জুতা", 1100, [
        ("৪১", "SNK-41", 1100, 12, 4),
        ("৪২", "SNK-42", 1100, 20, 4),
    ]),
    ("School Shoes Kids", "জুতা", 450, [
        ("২৮", "SKD-28", 450, 30, 8),
        ("৩০", "SKD-30", 450, 2, 5),
    ]),
    ("Canvas Tote Bag", "ব্যাগ", 380, [
        ("ডিফল্ট", "TOT-DEF", 380, 45, 10),
    ]),
    ("Ladies Handbag Leather", "ব্যাগ", 1800, [
        ("কালো", "HNB-BLK", 1800, 8, 3),
        ("বাদামি", "HNB-BRN", 1900, 5, 3),
    ]),
    ("School Backpack", "ব্যাগ", 720, [
        ("নীল", "BPK-BLU", 720, 20, 5),
        ("লাল", "BPK-RED", 720, 15, 5),
    ]),
    ("Samsung A15 Case Cover", "মোবাইল আক্সেসরিজ", 150, [
        ("ক্লিয়ার", "A15-CLR", 150, 60, 15),
        ("কালো", "A15-BLK", 150, 40, 15),
    ]),
    ("Bluetooth Earbuds TWS", "ইলেকট্রনিক্স", 1200, [
        ("সাদা", "TWS-WHT", 1200, 15, 3),
        ("কালো", "TWS-BLK", 1200, 12, 3),
    ]),
    ("Power Bank 10000mAh", "ইলেকট্রনিক্স", 900, [
        ("ডিফল্ট", "PBK-10K", 900, 20, 5),
    ]),
    ("USB Cable Type-C Fast Charge", "ইলেকট্রনিক্স", 180, [
        ("১ মিটার", "USB-1M", 180, 80, 20),
        ("২ মিটার", "USB-2M", 220, 50, 20),
    ]),
    ("Face Wash Neem 100ml", "সৌন্দর্য", 280, [
        ("ডিফল্ট", "FW-100", 280, 35, 8),
    ]),
    ("Whitening Cream SPF30", "সৌন্দর্য", 450, [
        ("৫০g", "WC-50G", 450, 25, 5),
    ]),
    ("Hair Oil Amla 200ml", "সৌন্দর্য", 220, [
        ("ডিফল্ট", "HO-200", 220, 40, 10),
    ]),
    ("Lipstick Matte Collection", "সৌন্দর্য", 350, [
        ("লাল #5", "LPS-R5", 350, 20, 5),
        ("পিঙ্ক #8", "LPS-P8", 350, 15, 5),
        ("নুড #12", "LPS-N12", 350, 0, 5),
    ]),
    ("Bed Sheet King Size Cotton", "গৃহস্থালি", 1100, [
        ("সাদা ফুল", "BDS-WFL", 1100, 10, 3),
        ("নীল চেক", "BDS-BLC", 1100, 8, 3),
    ]),
    ("Prayer Jaynamaz Premium", "ধর্মীয় পণ্য", 650, [
        ("সবুজ", "JAY-GRN", 650, 30, 8),
        ("লাল", "JAY-RED", 650, 20, 8),
    ]),
    ("Steel Tiffin Box 3 Layer", "গৃহস্থালি", 420, [
        ("ডিফল্ট", "TIF-3L", 420, 25, 5),
    ]),
    ("Mosquito Repellent Liquid", "গৃহস্থালি", 180, [
        ("৩০ রাত", "MOS-30N", 180, 50, 15),
    ]),
    ("Mixed Nuts Gift Pack 500g", "খাদ্যপণ্য", 850, [
        ("৫০০g", "NUT-500", 850, 8, 3),
        ("১ কেজি", "NUT-1K", 1600, 4, 2),
    ]),
    ("Honey Pure Sundarban 500g", "খাদ্যপণ্য", 750, [
        ("ডিফল্ট", "HON-500", 750, 2, 3),
    ]),
    # 5 extra products to reach 30
    ("Men's Polo T-Shirt", "পোশাক", 480, [
        ("S - সাদা", "POLO-S-WHT", 480, 22, 5),
        ("M - নেভি", "POLO-M-NVY", 480, 18, 5),
        ("L - লাল", "POLO-L-RED", 500, 10, 5),
    ]),
    ("Wireless Phone Charger 15W", "ইলেকট্রনিক্স", 650, [
        ("সাদা", "WC-15W-WHT", 650, 25, 5),
        ("কালো", "WC-15W-BLK", 650, 20, 5),
    ]),
    ("Organic Ghee 500ml", "খাদ্যপণ্য", 520, [
        ("৫০০ml", "GHE-500", 520, 15, 3),
        ("১ লিটার", "GHE-1L", 950, 8, 2),
    ]),
    ("Wall Clock Wooden", "গৃহস্থালি", 850, [
        ("ছোট ১২\"", "WCL-12", 850, 12, 3),
        ("বড় ১৬\"", "WCL-16", 1100, 6, 2),
    ]),
    ("Tasbeeh 99 Beads", "ধর্মীয় পণ্য", 180, [
        ("কাঠের", "TSB-WD", 180, 50, 10),
        ("পাথরের", "TSB-ST", 280, 30, 8),
        ("গোলাপি মুক্তা", "TSB-PRL", 450, 4, 3),
    ]),
]

# ── Helpers ─────────────────────────────────────────────────────────────────────

def gen_id(): return str(uuid.uuid4())
def gen_phone(): return f"+8801{random.randint(3,9)}{random.randint(10000000, 99999999)}"
def now_tz(): return datetime.now(timezone.utc)
def days_ago(n, jitter_hours=12):
    t = now_tz() - timedelta(days=n) + timedelta(hours=random.uniform(0, jitter_hours))
    return t
def order_number(i): return f"SM-{random.randint(100000, 999999)}-{i:04d}"

# ── Main Seed Function ───────────────────────────────────────────────────────────

async def seed():
    conn = await asyncpg.connect(DB_URL)
    print("Connected to PostgreSQL")

    # Get demo merchant
    merchant = await conn.fetchrow("SELECT id FROM merchants WHERE email = $1", DEMO_EMAIL)
    if not merchant:
        print("ERROR: Demo merchant not found. Register via the app first.")
        await conn.close()
        return
    mid = merchant["id"]
    print(f"Demo merchant ID: {mid}")

    # Clear existing data for this merchant
    print("Clearing existing demo data...")
    await conn.execute("DELETE FROM strategic_insights WHERE merchant_id = $1", mid)
    await conn.execute("DELETE FROM inventory_logs WHERE merchant_id = $1", mid)
    await conn.execute("DELETE FROM order_status_history WHERE order_id IN (SELECT id FROM orders WHERE merchant_id = $1)", mid)
    await conn.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE merchant_id = $1)", mid)
    await conn.execute("DELETE FROM orders WHERE merchant_id = $1", mid)
    await conn.execute("DELETE FROM customers WHERE merchant_id = $1", mid)
    await conn.execute("DELETE FROM product_variants WHERE product_id IN (SELECT id FROM products WHERE merchant_id = $1)", mid)
    await conn.execute("DELETE FROM products WHERE merchant_id = $1", mid)
    print("Old data cleared.")

    # ── PRODUCTS ────────────────────────────────────────────────────────────────
    print("Creating 30 products with 60+ variants...")
    all_variants = []  # [(product_id, variant_id, name, price, stock)]

    for i, (pname, pcat, pbase, pvariants) in enumerate(PRODUCT_CATALOG):
        pid = gen_id()
        await conn.execute("""
            INSERT INTO products (id, merchant_id, name, category, base_price, is_active, is_published, total_sold, image_urls)
            VALUES ($1, $2, $3, $4, $5, TRUE, TRUE, 0, $6)
        """, pid, mid, pname, pcat, Decimal(str(pbase)), [])

        for vname, vsku, vprice, vstock, vlow in pvariants:
            vid = gen_id()
            await conn.execute("""
                INSERT INTO product_variants (id, product_id, name, sku, price, stock_quantity, low_stock_alert, attributes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            """, vid, pid, vname, vsku, Decimal(str(vprice)), vstock, vlow, json.dumps({}))
            all_variants.append({
                "product_id": pid, "variant_id": vid,
                "product_name": pname, "variant_name": vname,
                "price": Decimal(str(vprice)), "stock": vstock,
            })

    print(f"  Created {len(PRODUCT_CATALOG)} products, {len(all_variants)} variants")

    # ── CUSTOMERS ───────────────────────────────────────────────────────────────
    print("Creating 100 customers...")
    cust_ids = []
    sources = ["MANUAL", "FACEBOOK", "WHATSAPP", "INSTAGRAM", "WALK_IN"]
    source_weights = [0.15, 0.35, 0.30, 0.15, 0.05]

    # Track used phones for uniqueness
    used_phones = set()

    # Create "suspicious" customers (will cancel many orders)
    suspicious_phones = ["+8801312345001", "+8801412345002", "+8801512345003"]

    all_customers = []

    # 3 suspicious customers first
    for sph in suspicious_phones:
        cid = gen_id()
        cname = random.choice(BD_NAMES)
        district = random.choice(list(BD_DISTRICTS[:10]))
        division = BD_DIVISIONS.get(district, "ঢাকা")
        await conn.execute("""
            INSERT INTO customers (id, merchant_id, name, phone, district, division,
                                   total_orders, total_spent, tags, source)
            VALUES ($1, $2, $3, $4, $5, $6, 0, 0, $7, $8)
        """, cid, mid, cname, sph, district, division, ["সন্দেহজনক"], "FACEBOOK")
        all_customers.append({"id": cid, "name": cname, "phone": sph, "suspicious": True})
        used_phones.add(sph)

    # 97 regular customers
    for i in range(97):
        phone = gen_phone()
        while phone in used_phones:
            phone = gen_phone()
        used_phones.add(phone)

        cid = gen_id()
        cname = BD_NAMES[i % len(BD_NAMES)]
        district = random.choice(BD_DISTRICTS[:40])
        division = BD_DIVISIONS.get(district, "ঢাকা")
        src = random.choices(sources, weights=source_weights)[0]

        tags = []
        if i < 15:
            tags = ["VIP", "নিয়মিত"]
        elif i < 30:
            tags = ["নিয়মিত"]
        elif i < 50:
            tags = ["নতুন"]

        await conn.execute("""
            INSERT INTO customers (id, merchant_id, name, phone, district, division,
                                   total_orders, total_spent, tags, source)
            VALUES ($1, $2, $3, $4, $5, $6, 0, 0, $7, $8)
        """, cid, mid, cname, phone, district, division, tags, src)
        all_customers.append({"id": cid, "name": cname, "phone": phone, "suspicious": False})

    print(f"  Created {len(all_customers)} customers")

    # ── ORDERS ──────────────────────────────────────────────────────────────────
    print("Creating 180 orders over 30 days...")

    channels = ["FACEBOOK", "WHATSAPP", "INSTAGRAM", "MANUAL", "WEBSITE"]
    ch_weights = [0.38, 0.28, 0.16, 0.12, 0.06]

    pay_methods = ["COD", "BKASH", "NAGAD", "ROCKET", "BANK_TRANSFER"]
    pm_weights = [0.40, 0.30, 0.18, 0.08, 0.04]

    # Order plan — distribute 180 orders over 30 days
    # Day 0 (today) = sparse, Day 1-29 = normal, with a spike day on day 8
    order_days = (
        [0] * 4 +   # today: 4 orders
        [1] * 5 +   # yesterday: 5
        [2] * 7 + [3] * 6 + [4] * 6 + [5] * 6 + [6] * 7 + [7] * 6 +
        [8] * 20 +  # spike day: 20 orders (fraud pattern)
        [9] * 6 + [10] * 6 + [11] * 6 + [12] * 5 + [13] * 6 + [14] * 6 +
        [15] * 5 + [16] * 5 + [17] * 5 + [18] * 5 + [19] * 4 + [20] * 4 +
        [21] * 4 + [22] * 4 + [23] * 3 + [24] * 3 + [25] * 3 + [26] * 3 +
        [27] * 3 + [28] * 3 + [29] * 3
    )
    random.shuffle(order_days[:60])  # mix first 60 slightly

    # Status assignment
    def pick_status(day_age):
        """Older orders more likely delivered/cancelled, recent ones pending."""
        if day_age <= 1:
            return random.choices(
                ["PENDING", "CONFIRMED", "PROCESSING"],
                weights=[0.7, 0.2, 0.1]
            )[0]
        elif day_age <= 5:
            return random.choices(
                ["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "PENDING"],
                weights=[0.2, 0.25, 0.25, 0.2, 0.1]
            )[0]
        else:
            return random.choices(
                ["DELIVERED", "CANCELLED", "SHIPPED", "RETURNED"],
                weights=[0.55, 0.20, 0.15, 0.10]
            )[0]

    # Customer assignment — VIP customers get multiple orders
    def pick_customer(order_idx, is_spike_day=False):
        if is_spike_day:
            # Spike day: mix of normal and suspicious
            if random.random() < 0.4:
                return random.choice([c for c in all_customers if c["suspicious"]])
        # VIP customers (first 15) get ~20% of all orders
        if random.random() < 0.22 and order_idx > 5:
            return random.choice(all_customers[:15])
        return random.choice(all_customers[3:])  # skip suspicious for normal orders

    total_sold_update = {}   # variant_id -> total_sold
    cust_order_counts = {}   # cust_id -> (count, total_spent)
    order_number_counter = random.randint(1000, 5000)

    for order_idx, day_age in enumerate(order_days):
        is_spike = (day_age == 8)
        cust = pick_customer(order_idx, is_spike)

        # For suspicious customers, force more cancellations
        if cust["suspicious"]:
            status_str = random.choices(
                ["CANCELLED", "PENDING", "DELIVERED"],
                weights=[0.65, 0.25, 0.10]
            )[0]
        else:
            status_str = pick_status(day_age)

        # Pick 1-3 products for this order
        num_items = random.choices([1, 2, 3], weights=[0.55, 0.30, 0.15])[0]
        order_items = random.sample(all_variants, min(num_items, len(all_variants)))

        # Calculate amounts
        subtotal = sum(v["price"] * random.randint(1, 3) for v in order_items)
        item_qtys = [random.randint(1, 2) for _ in order_items]
        subtotal = sum(v["price"] * q for v, q in zip(order_items, item_qtys))
        discount = Decimal("0")
        if random.random() < 0.25 and subtotal > 500:
            discount = Decimal(str(random.choice([50, 100, 150, 200])))
        shipping = Decimal("60") if random.random() < 0.7 else Decimal("0")
        total = subtotal - discount + shipping

        # Payment
        pay_method = random.choices(pay_methods, weights=pm_weights)[0]
        if status_str == "DELIVERED":
            if pay_method == "COD":
                # 80% fully paid, 20% unpaid (bad actors)
                if random.random() < 0.80:
                    paid = total
                    pay_status = "PAID"
                else:
                    paid = Decimal("0")
                    pay_status = "UNPAID"
            else:
                paid = total
                pay_status = "PAID"
        elif status_str == "CANCELLED":
            paid = Decimal("0")
            pay_status = "UNPAID"
        elif status_str in ("SHIPPED", "PROCESSING", "CONFIRMED"):
            if pay_method != "COD":
                if random.random() < 0.7:
                    paid = total
                    pay_status = "PAID"
                else:
                    paid = total * Decimal("0.5")
                    pay_status = "PARTIAL"
            else:
                paid = Decimal("0")
                pay_status = "UNPAID"
        else:  # PENDING, RETURNED
            paid = Decimal("0")
            pay_status = "UNPAID"

        due = total - paid
        channel = random.choices(channels, weights=ch_weights)[0]
        district = random.choice(BD_DISTRICTS[:15])
        division = BD_DIVISIONS.get(district, "ঢাকা")

        created_at = days_ago(day_age)
        delivered_at = None
        if status_str == "DELIVERED":
            delivered_at = created_at + timedelta(days=random.randint(2, 5))

        oid = gen_id()
        order_number_counter += 1

        # Stale unpaid orders (15 orders >7 days old, COD, UNPAID) for fraud pattern
        if order_idx < 15 and day_age > 7:
            pay_method = "COD"
            pay_status = "UNPAID"
            paid = Decimal("0")
            due = total
            if status_str == "DELIVERED":
                status_str = "SHIPPED"

        await conn.execute("""
            INSERT INTO orders (
                id, merchant_id, customer_id, order_number, status, channel,
                subtotal, discount_amount, shipping_cost, total_amount,
                paid_amount, due_amount, payment_method, payment_status,
                delivery_address, delivery_district, delivery_division,
                delivered_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16, $17,
                $18, $19, $20
            )
        """,
            oid, mid, cust["id"], order_number(order_number_counter),
            status_str, channel,
            subtotal, discount, shipping, total,
            paid, due, pay_method, pay_status,
            f"{district}, {division}", district, division,
            delivered_at, created_at, created_at
        )

        # Order items
        for variant, qty in zip(order_items, item_qtys):
            iid = gen_id()
            unit_p = variant["price"]
            total_p = unit_p * qty
            await conn.execute("""
                INSERT INTO order_items (id, order_id, product_id, variant_id,
                    product_name, variant_name, quantity, unit_price, total_price)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, iid, oid, variant["product_id"], variant["variant_id"],
                variant["product_name"], variant["variant_name"],
                qty, unit_p, total_p)

            if status_str == "DELIVERED":
                total_sold_update[variant["variant_id"]] = (
                    total_sold_update.get(variant["variant_id"], 0) + qty
                )

        # Status history
        hist_id = gen_id()
        await conn.execute("""
            INSERT INTO order_status_history (id, order_id, status, note, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, hist_id, oid, "PENDING", "অর্ডার তৈরি হয়েছে", created_at)

        if status_str != "PENDING":
            statuses_chain = {
                "CONFIRMED": ["CONFIRMED"],
                "PROCESSING": ["CONFIRMED", "PROCESSING"],
                "SHIPPED": ["CONFIRMED", "PROCESSING", "SHIPPED"],
                "DELIVERED": ["CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"],
                "CANCELLED": ["CANCELLED"],
                "RETURNED": ["CONFIRMED", "SHIPPED", "RETURNED"],
            }
            chain = statuses_chain.get(status_str, [status_str])
            for j, s in enumerate(chain):
                hist2_id = gen_id()
                h_time = created_at + timedelta(hours=(j + 1) * random.randint(4, 20))
                await conn.execute("""
                    INSERT INTO order_status_history (id, order_id, status, note, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                """, hist2_id, oid, s, None, h_time)

        # Update customer stats
        cust_id = cust["id"]
        if cust_id not in cust_order_counts:
            cust_order_counts[cust_id] = {"count": 0, "spent": Decimal("0"), "last_at": None}
        cust_order_counts[cust_id]["count"] += 1
        if status_str == "DELIVERED":
            cust_order_counts[cust_id]["spent"] += total
        if (cust_order_counts[cust_id]["last_at"] is None or
                created_at > cust_order_counts[cust_id]["last_at"]):
            cust_order_counts[cust_id]["last_at"] = created_at

    print(f"  Created {len(order_days)} orders (target: 180)")

    # ── UPDATE CUSTOMER TOTALS ───────────────────────────────────────────────────
    print("Updating customer totals...")
    for cust_id, stats in cust_order_counts.items():
        await conn.execute("""
            UPDATE customers SET total_orders = $1, total_spent = $2, last_order_at = $3
            WHERE id = $4
        """, stats["count"], stats["spent"], stats["last_at"], cust_id)

    # ── INVENTORY LOGS ──────────────────────────────────────────────────────────
    print("Creating inventory logs...")
    log_count = 0
    for v in all_variants:
        vid = v["variant_id"]
        initial_stock = v["stock"] + total_sold_update.get(vid, 0) + random.randint(0, 10)

        # Initial STOCK_IN log
        log_id = gen_id()
        await conn.execute("""
            INSERT INTO inventory_logs (
                id, merchant_id, variant_id, type,
                quantity_before, quantity_change, quantity_after,
                reason, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, log_id, mid, vid, "STOCK_IN",
            0, initial_stock, initial_stock,
            "প্রাথমিক স্টক লোড",
            days_ago(35, 2))
        log_count += 1

        # SALE logs for delivered orders
        sold = total_sold_update.get(vid, 0)
        if sold > 0:
            log_id2 = gen_id()
            after_sale = initial_stock - sold
            await conn.execute("""
                INSERT INTO inventory_logs (
                    id, merchant_id, variant_id, type,
                    quantity_before, quantity_change, quantity_after,
                    reason, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, log_id2, mid, vid, "SALE",
                initial_stock, -sold, max(0, after_sale),
                "বিক্রয় থেকে বিয়োগ",
                days_ago(1, 2))
            log_count += 1

        # Random ADJUSTMENT for some variants
        if random.random() < 0.2 and v["stock"] > 5:
            adj = random.choice([-5, -3, -2, 3, 5, 10])
            before = v["stock"]
            after = max(0, before + adj)
            log_id3 = gen_id()
            await conn.execute("""
                INSERT INTO inventory_logs (
                    id, merchant_id, variant_id, type,
                    quantity_before, quantity_change, quantity_after,
                    reason, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, log_id3, mid, vid, "ADJUSTMENT",
                before, adj, after,
                "ম্যানুয়াল সমন্বয়",
                days_ago(random.randint(3, 15), 4))
            log_count += 1

    print(f"  Created {log_count} inventory log entries")

    # ── FINAL STATS ─────────────────────────────────────────────────────────────
    total_orders = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1", mid)
    total_customers = await conn.fetchval("SELECT COUNT(*) FROM customers WHERE merchant_id = $1", mid)
    total_products = await conn.fetchval("SELECT COUNT(*) FROM products WHERE merchant_id = $1", mid)
    delivered = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1 AND status = 'DELIVERED'", mid)
    cancelled = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1 AND status = 'CANCELLED'", mid)
    paid = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1 AND payment_status = 'PAID'", mid)

    sep = "=" * 42
    print(f"\n{sep}")
    print("DONE: Demo data seeded successfully!")
    print(f"  Products:  {total_products}")
    print(f"  Customers: {total_customers}")
    print(f"  Orders:    {total_orders} total")
    print(f"    -> {delivered} delivered ({100*delivered//total_orders}%)")
    print(f"    -> {cancelled} cancelled ({100*cancelled//total_orders}%)")
    print(f"    -> {paid} paid ({100*paid//total_orders}%)")
    print(f"  Inventory: {log_count} movement logs")
    print(sep)
    print("Next: Trigger AI agents via POST /api/v1/ai/strategic/run")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
