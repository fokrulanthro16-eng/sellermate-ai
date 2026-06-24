"""
Local AI fallback — used when ANTHROPIC_API_KEY is absent.
Queries the DB directly and returns a coherent Bengali/English response.
"""
from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.order import Order, OrderItem, OrderStatus
from app.models.customer import Customer
from app.models.product import Product, ProductVariant


def _detect_lang(text: str) -> str:
    return "bn" if re.search(r"[ঀ-৿]", text) else "en"


def _kw(text: str, *words: str) -> bool:
    t = text.lower()
    return any(w in t for w in words)


async def _get_today_summary(db: AsyncSession, merchant_id: str) -> dict:
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        ).where(
            Order.merchant_id == merchant_id,
            func.date(Order.created_at) == today,
        )
    )
    row = result.one()
    pending = await db.execute(
        select(func.count(Order.id)).where(
            Order.merchant_id == merchant_id,
            Order.status == OrderStatus.PENDING,
        )
    )
    return {
        "count": int(row.count),
        "revenue": float(row.revenue),
        "pending": int(pending.scalar() or 0),
    }


async def _get_inventory_alerts(db: AsyncSession, merchant_id: str) -> dict:
    low = await db.execute(
        select(func.count(ProductVariant.id))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            Product.merchant_id == merchant_id,
            ProductVariant.stock_quantity > 0,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
    )
    out = await db.execute(
        select(func.count(ProductVariant.id))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            Product.merchant_id == merchant_id,
            ProductVariant.stock_quantity == 0,
        )
    )
    return {"low": int(low.scalar() or 0), "out": int(out.scalar() or 0)}


async def _get_orders_summary(db: AsyncSession, merchant_id: str, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(Order.id).label("total"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        ).where(
            Order.merchant_id == merchant_id,
            Order.created_at >= since,
        )
    )
    row = result.one()

    status_counts: dict[str, int] = {}
    for status in [OrderStatus.PENDING, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        cnt = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.status == status,
                Order.created_at >= since,
            )
        )
        status_counts[status.value] = int(cnt.scalar() or 0)

    return {
        "total": int(row.total),
        "revenue": float(row.revenue),
        "status": status_counts,
        "days": days,
    }


async def _get_top_products(db: AsyncSession, merchant_id: str, limit: int = 5) -> list[dict]:
    result = await db.execute(
        select(Product.name, func.sum(OrderItem.quantity).label("sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Product.merchant_id == merchant_id, Order.status == OrderStatus.DELIVERED)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    return [{"name": r.name, "sold": int(r.sold)} for r in result.all()]


async def _get_customer_count(db: AsyncSession, merchant_id: str) -> dict:
    total = await db.execute(
        select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
    )
    repeat = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.total_orders >= 2,
        )
    )
    try:
        vip = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.merchant_id == merchant_id,
                Customer.tags.contains(["VIP"]),
            )
        )
        vip_count = int(vip.scalar() or 0)
    except Exception:
        vip_count = 0

    return {
        "total": int(total.scalar() or 0),
        "repeat": int(repeat.scalar() or 0),
        "vip": vip_count,
    }


async def _get_low_stock_variants(db: AsyncSession, merchant_id: str, limit: int = 5) -> list[dict]:
    result = await db.execute(
        select(Product.name, ProductVariant.name.label("variant_name"), ProductVariant.stock_quantity)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .where(
            Product.merchant_id == merchant_id,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .order_by(ProductVariant.stock_quantity.asc())
        .limit(limit)
    )
    items = []
    for r in result.all():
        name = r.name
        if r.variant_name and r.variant_name != r.name:
            name += f" – {r.variant_name}"
        items.append({"name": name, "qty": int(r.stock_quantity)})
    return items


def _fmt(amount: float) -> str:
    return f"৳{amount:,.0f}"


async def generate_response(merchant: Merchant, user_message: str, db: AsyncSession) -> str:
    lang = _detect_lang(user_message)
    msg = user_message.lower()
    mid = str(merchant.id)

    # --- GREETING ---
    if _kw(msg, "হ্যালো", "হ্যাই", "হেলো", "সালাম", "hello", "hi", "hey", "salam"):
        if lang == "bn":
            return (
                f"আস-সালামু আলাইকুম! আমি SellerMate AI। 😊\n\n"
                f"**{merchant.business_name}**-এ আপনাকে স্বাগতম!\n\n"
                f"আমি আপনাকে সাহায্য করতে পারি:\n"
                f"- 📦 স্টক ও ইনভেন্টরি পরীক্ষা\n"
                f"- 🛒 অর্ডার পর্যালোচনা\n"
                f"- 👥 গ্রাহক তথ্য\n"
                f"- 📊 বিক্রয় বিশ্লেষণ\n\n"
                f"কী জানতে চান?"
            )
        return (
            f"Hello! I'm SellerMate AI — your business assistant. 😊\n\n"
            f"Welcome to **{merchant.business_name}**!\n\n"
            f"I can help you with:\n"
            f"- 📦 Stock & inventory checks\n"
            f"- 🛒 Order reviews\n"
            f"- 👥 Customer information\n"
            f"- 📊 Sales analysis\n\n"
            f"What would you like to know?"
        )

    # --- TODAY SUMMARY ---
    if _kw(msg, "আজ", "সারাংশ", "summary", "today", "overview", "আজকের"):
        today = await _get_today_summary(db, mid)
        inv = await _get_inventory_alerts(db, mid)
        if lang == "bn":
            parts = [
                f"## 📊 আজকের সারাংশ — {merchant.business_name}\n",
                f"- 🛒 অর্ডার: **{today['count']}টি**",
                f"- 💰 রাজস্ব: **{_fmt(today['revenue'])}**",
                f"- ⏳ পেন্ডিং: **{today['pending']}টি**",
            ]
        else:
            parts = [
                f"## 📊 Today's Summary — {merchant.business_name}\n",
                f"- 🛒 Orders: **{today['count']}**",
                f"- 💰 Revenue: **{_fmt(today['revenue'])}**",
                f"- ⏳ Pending: **{today['pending']}**",
            ]
        if inv["out"] > 0:
            parts.append(f"- ⚠️ {'স্টকশূন্য' if lang == 'bn' else 'Out of stock'}: **{inv['out']}**")
        if inv["low"] > 0:
            parts.append(f"- 🔶 {'কম স্টক' if lang == 'bn' else 'Low stock alerts'}: **{inv['low']}**")
        if inv["out"] == 0 and inv["low"] == 0:
            parts.append(f"- ✅ {'ইনভেন্টরি সুস্থ' if lang == 'bn' else 'Inventory healthy'}")
        return "\n".join(parts)

    # --- STOCK / INVENTORY ---
    if _kw(msg, "স্টক", "ইনভেন্টরি", "stock", "inventory", "কম স্টক", "low stock", "শেষ"):
        inv = await _get_inventory_alerts(db, mid)
        low_items = await _get_low_stock_variants(db, mid, limit=5)
        if lang == "bn":
            if inv["out"] == 0 and inv["low"] == 0:
                return "✅ সব পণ্যের স্টক পর্যাপ্ত! কোনো সতর্কতা নেই।"
            parts = ["## 📦 স্টক রিপোর্ট\n"]
            if inv["out"] > 0:
                parts.append(f"🔴 **স্টকশূন্য**: {inv['out']}টি ভ্যারিয়েন্ট")
            if inv["low"] > 0:
                parts.append(f"🟡 **কম স্টক**: {inv['low']}টি ভ্যারিয়েন্ট")
        else:
            if inv["out"] == 0 and inv["low"] == 0:
                return "✅ All products are adequately stocked — no alerts."
            parts = ["## 📦 Stock Report\n"]
            if inv["out"] > 0:
                parts.append(f"🔴 **Out of stock**: {inv['out']} variants")
            if inv["low"] > 0:
                parts.append(f"🟡 **Low stock**: {inv['low']} variants")

        if low_items:
            parts.append(f"\n**{'বিস্তারিত' if lang == 'bn' else 'Details'}:**")
            for item in low_items:
                if lang == "bn":
                    qty_label = "শেষ" if item["qty"] == 0 else f"{item['qty']}টি বাকি"
                else:
                    qty_label = "out of stock" if item["qty"] == 0 else f"{item['qty']} remaining"
                parts.append(f"- {item['name']}: {qty_label}")
        return "\n".join(parts)

    # --- ORDERS ---
    if _kw(msg, "অর্ডার", "order", "বিক্রয়", "sales", "ডেলিভার", "deliver", "বাতিল", "cancel"):
        days = 30 if _kw(msg, "৩০", "30", "মাস", "month") else 7
        summary = await _get_orders_summary(db, mid, days=days)
        if lang == "bn":
            parts = [
                f"## 🛒 অর্ডার রিপোর্ট — শেষ {days} দিন\n",
                f"- মোট অর্ডার: **{summary['total']}টি**",
                f"- মোট রাজস্ব: **{_fmt(summary['revenue'])}**",
            ]
            labels = {
                OrderStatus.PENDING.value: "⏳ পেন্ডিং",
                OrderStatus.DELIVERED.value: "✅ ডেলিভার্ড",
                OrderStatus.CANCELLED.value: "❌ বাতিল",
            }
        else:
            parts = [
                f"## 🛒 Order Report — Last {days} days\n",
                f"- Total orders: **{summary['total']}**",
                f"- Total revenue: **{_fmt(summary['revenue'])}**",
            ]
            labels = {
                OrderStatus.PENDING.value: "⏳ Pending",
                OrderStatus.DELIVERED.value: "✅ Delivered",
                OrderStatus.CANCELLED.value: "❌ Cancelled",
            }
        for status, label in labels.items():
            count = summary["status"].get(status, 0)
            if count:
                parts.append(f"- {label}: **{count}{'টি' if lang == 'bn' else ''}**")
        if summary["total"] > 0:
            cancel_rate = summary["status"].get(OrderStatus.CANCELLED.value, 0) / summary["total"] * 100
            if cancel_rate > 20:
                warn = (
                    f"\n⚠️ বাতিলের হার **{cancel_rate:.0f}%** — এটি বেশি। কারণ খুঁজে দেখুন।"
                    if lang == "bn"
                    else f"\n⚠️ Cancellation rate **{cancel_rate:.0f}%** is high — investigate causes."
                )
                parts.append(warn)
        return "\n".join(parts)

    # --- CUSTOMERS ---
    if _kw(msg, "গ্রাহক", "customer", "ক্লায়েন্ট", "vip", "ভিআইপি"):
        cust = await _get_customer_count(db, mid)
        if lang == "bn":
            parts = [
                f"## 👥 গ্রাহক তথ্য\n",
                f"- মোট গ্রাহক: **{cust['total']}জন**",
                f"- নিয়মিত গ্রাহক (২+ অর্ডার): **{cust['repeat']}জন**",
                f"- ভিআইপি গ্রাহক: **{cust['vip']}জন**",
            ]
            if cust["total"] > 0:
                repeat_pct = cust["repeat"] / cust["total"] * 100
                parts.append(f"\n📈 রিটেনশন রেট: **{repeat_pct:.0f}%**")
                advice = "✅ চমৎকার!" if repeat_pct >= 30 else "💡 অফার পাঠিয়ে গ্রাহক ধরে রাখুন।"
                parts.append(advice)
        else:
            parts = [
                f"## 👥 Customer Overview\n",
                f"- Total customers: **{cust['total']}**",
                f"- Repeat customers (2+ orders): **{cust['repeat']}**",
                f"- VIP customers: **{cust['vip']}**",
            ]
            if cust["total"] > 0:
                repeat_pct = cust["repeat"] / cust["total"] * 100
                parts.append(f"\n📈 Retention rate: **{repeat_pct:.0f}%**")
                advice = "✅ Excellent! Retention is strong." if repeat_pct >= 30 else "💡 Send offers to improve retention."
                parts.append(advice)
        return "\n".join(parts)

    # --- PRODUCTS / TOP ---
    if _kw(msg, "পণ্য", "product", "item", "টপ", "top", "বেস্ট", "best", "বিক্রি"):
        top = await _get_top_products(db, mid, limit=5)
        if lang == "bn":
            if not top:
                return "এখনো কোনো ডেলিভার্ড অর্ডার নেই — শীর্ষ পণ্য দেখানো যাচ্ছে না।"
            parts = ["## 🏆 শীর্ষ বিক্রিত পণ্য\n"]
            for i, p in enumerate(top, 1):
                parts.append(f"{i}. **{p['name']}** — {p['sold']}টি বিক্রিত")
        else:
            if not top:
                return "No delivered orders yet — top products unavailable."
            parts = ["## 🏆 Top Selling Products\n"]
            for i, p in enumerate(top, 1):
                parts.append(f"{i}. **{p['name']}** — {p['sold']} sold")
        return "\n".join(parts)

    # --- REVENUE / ANALYTICS ---
    if _kw(msg, "রাজস্ব", "revenue", "আয়", "income", "profit", "লাভ", "বিশ্লেষণ", "analytics", "রিপোর্ট", "report"):
        days = 30 if _kw(msg, "মাস", "month", "৩০", "30") else 7
        summary = await _get_orders_summary(db, mid, days=days)
        top = await _get_top_products(db, mid, limit=3)
        if lang == "bn":
            parts = [
                f"## 📊 রাজস্ব বিশ্লেষণ — শেষ {days} দিন\n",
                f"- মোট রাজস্ব: **{_fmt(summary['revenue'])}**",
                f"- মোট অর্ডার: **{summary['total']}টি**",
            ]
            if summary["total"] > 0:
                parts.append(f"- গড় অর্ডার মূল্য: **{_fmt(summary['revenue'] / summary['total'])}**")
        else:
            parts = [
                f"## 📊 Revenue Analysis — Last {days} days\n",
                f"- Total revenue: **{_fmt(summary['revenue'])}**",
                f"- Total orders: **{summary['total']}**",
            ]
            if summary["total"] > 0:
                parts.append(f"- Avg order value: **{_fmt(summary['revenue'] / summary['total'])}**")
        if top:
            label = "শীর্ষ পণ্য" if lang == "bn" else "Top products"
            parts.append(f"\n**{label}:** {', '.join(p['name'] for p in top)}")
        return "\n".join(parts)

    # --- STRATEGIC / AI CENTER ---
    if _kw(msg, "ট্রাস্ট", "trust", "ফ্রড", "fraud", "ঝুঁকি", "risk", "কৌশল", "strategic"):
        if lang == "bn":
            return (
                "## 🛡️ কৌশলগত এআই বিশ্লেষণ\n\n"
                "**এআই সেন্টার** পেজে যান সম্পূর্ণ বিশ্লেষণের জন্য:\n\n"
                "- 📈 **ট্রাস্ট গ্রাফ** — ব্যবসার বিশ্বাসযোগ্যতা\n"
                "- 🚨 **ফ্রড সেন্টিনেল** — সন্দেহজনক অর্ডার\n"
                "- 💡 **কৌশলগত অন্তর্দৃষ্টি** — AI পরামর্শ"
            )
        return (
            "## 🛡️ Strategic AI Analysis\n\n"
            "Visit the **AI Center** page for full analysis:\n\n"
            "- 📈 **Trust Graph** — Business reliability score\n"
            "- 🚨 **Fraud Sentinel** — Suspicious order alerts\n"
            "- 💡 **Strategic Insights** — AI recommendations"
        )

    # --- HELP ---
    if _kw(msg, "help", "সাহায্য", "কী পারো", "কি করতে", "what can"):
        if lang == "bn":
            return (
                "## 🤖 আমি যা করতে পারি\n\n"
                "- **আজকের সারাংশ** → 'আজকের অর্ডার কেমন?'\n"
                "- **স্টক চেক** → 'কম স্টক আছে কী?'\n"
                "- **অর্ডার রিপোর্ট** → 'এই সপ্তাহের অর্ডার দেখাও'\n"
                "- **গ্রাহক তথ্য** → 'ভিআইপি গ্রাহক কতজন?'\n"
                "- **শীর্ষ পণ্য** → 'কোন পণ্য সবচেয়ে বেশি বিক্রি?'\n"
                "- **রাজস্ব** → 'এই মাসে কত আয় হয়েছে?'"
            )
        return (
            "## 🤖 What I Can Do\n\n"
            "- **Today's summary** → 'How are today's orders?'\n"
            "- **Stock check** → 'Are there low stock items?'\n"
            "- **Order report** → 'Show this week's orders'\n"
            "- **Customer info** → 'How many VIP customers?'\n"
            "- **Top products** → 'Which product sells most?'\n"
            "- **Revenue** → 'How much did I earn this month?'"
        )

    # --- DEFAULT: show today summary ---
    today = await _get_today_summary(db, mid)
    inv = await _get_inventory_alerts(db, mid)
    if lang == "bn":
        parts = [
            f"আমি নিশ্চিত নই — এখানে আজকের সারাংশ:\n",
            f"- অর্ডার: **{today['count']}টি** | রাজস্ব: **{_fmt(today['revenue'])}**",
            f"- পেন্ডিং: **{today['pending']}টি**",
        ]
        if inv["low"] or inv["out"]:
            parts.append(f"- স্টক সতর্কতা: কম {inv['low']}টি | শেষ {inv['out']}টি")
        parts.append("\nআরো নির্দিষ্টভাবে প্রশ্ন করুন!")
    else:
        parts = [
            f"Not sure what you meant — here's today's quick summary:\n",
            f"- Orders: **{today['count']}** | Revenue: **{_fmt(today['revenue'])}**",
            f"- Pending: **{today['pending']}**",
        ]
        if inv["low"] or inv["out"]:
            parts.append(f"- Stock alerts: low {inv['low']} | out {inv['out']}")
        parts.append("\nFeel free to ask something more specific!")
    return "\n".join(parts)


async def stream_fallback(
    merchant: Merchant,
    user_message: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    try:
        text = await generate_response(merchant, user_message, db)
    except Exception as exc:
        text = f"⚠️ দুঃখিত, একটি ত্রুটি ঘটেছে: {exc}" if _detect_lang(user_message) == "bn" else f"⚠️ Sorry, an error occurred: {exc}"

    words = text.split(" ")
    buf = ""
    for i, word in enumerate(words):
        buf += ("" if i == 0 else " ") + word
        if len(buf) >= 20 or i == len(words) - 1:
            yield buf
            buf = ""
