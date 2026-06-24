"""
Package-based AI Engine — smart fallback when no LLM API key is configured.

Uses:
  - rapidfuzz  : intent detection (via intent_detector.py)
  - numpy      : linear-regression trend detection on daily revenue
  - Real DB    : all numbers come from the database; nothing is invented

Streams the response in ~30-char chunks (matching the existing streaming contract).
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.intent_detector import IntentResult, detect_intent
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product, ProductVariant

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ── Formatting helpers ─────────────────────────────────────

def _fmt(amount: float) -> str:
    return f"৳{amount:,.0f}"


# ── DB query helpers ───────────────────────────────────────

async def _today_stats(db: AsyncSession, mid: str) -> dict:
    today = datetime.now(timezone.utc).date()
    r = await db.execute(
        select(
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        ).where(Order.merchant_id == mid, func.date(Order.created_at) == today)
    )
    row = r.one()
    pending = await db.execute(
        select(func.count(Order.id)).where(
            Order.merchant_id == mid, Order.status == OrderStatus.PENDING
        )
    )
    return {
        "count": int(row.count),
        "revenue": float(row.revenue),
        "pending": int(pending.scalar() or 0),
    }


async def _inventory_alerts(db: AsyncSession, mid: str) -> dict:
    low = await db.execute(
        select(func.count(ProductVariant.id))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            Product.merchant_id == mid,
            ProductVariant.stock_quantity > 0,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
    )
    out = await db.execute(
        select(func.count(ProductVariant.id))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(Product.merchant_id == mid, ProductVariant.stock_quantity == 0)
    )
    return {"low": int(low.scalar() or 0), "out": int(out.scalar() or 0)}


async def _low_stock_items(db: AsyncSession, mid: str, limit: int = 7) -> list[dict]:
    result = await db.execute(
        select(
            Product.name,
            ProductVariant.name.label("vname"),
            ProductVariant.stock_quantity,
        )
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .where(
            Product.merchant_id == mid,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .order_by(ProductVariant.stock_quantity.asc())
        .limit(limit)
    )
    items = []
    for r in result.all():
        display = r.name + (f" – {r.vname}" if r.vname and r.vname != r.name else "")
        items.append({"name": display, "qty": int(r.stock_quantity)})
    return items


async def _order_stats(db: AsyncSession, mid: str, days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    r = await db.execute(
        select(
            func.count(Order.id).label("total"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.coalesce(func.avg(Order.total_amount), 0).label("avg_value"),
        ).where(Order.merchant_id == mid, Order.created_at >= since)
    )
    row = r.one()
    status_counts: dict[str, int] = {}
    for status in [OrderStatus.PENDING, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED]:
        cnt = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == mid,
                Order.status == status,
                Order.created_at >= since,
            )
        )
        status_counts[status.value] = int(cnt.scalar() or 0)
    return {
        "total": int(row.total),
        "revenue": float(row.revenue),
        "avg_value": float(row.avg_value),
        "status": status_counts,
        "days": days,
    }


async def _daily_revenue(db: AsyncSession, mid: str, days: int = 30) -> list[float]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date_trunc("day", Order.created_at).label("day"),
            func.coalesce(func.sum(Order.total_amount), 0).label("rev"),
        )
        .where(Order.merchant_id == mid, Order.created_at >= since)
        .group_by(func.date_trunc("day", Order.created_at))
        .order_by(func.date_trunc("day", Order.created_at))
    )
    return [float(r.rev) for r in result.all()]


async def _top_products(db: AsyncSession, mid: str, days: int = 30, limit: int = 5) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            Product.name,
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.total_price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Product.merchant_id == mid,
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= since,
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.total_price).desc())
        .limit(limit)
    )
    return [{"name": r.name, "units": int(r.units), "revenue": float(r.revenue)} for r in result.all()]


async def _customer_stats(db: AsyncSession, mid: str) -> dict:
    total = await db.execute(
        select(func.count(Customer.id)).where(Customer.merchant_id == mid)
    )
    repeat = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == mid, Customer.total_orders >= 2
        )
    )
    top_cust = await db.execute(
        select(Customer.name, Customer.total_orders, Customer.total_spent)
        .where(Customer.merchant_id == mid)
        .order_by(Customer.total_spent.desc())
        .limit(5)
    )
    top_list = [
        {"name": r.name or "—", "orders": int(r.total_orders), "spent": float(r.total_spent)}
        for r in top_cust.all()
    ]
    return {
        "total": int(total.scalar() or 0),
        "repeat": int(repeat.scalar() or 0),
        "top": top_list,
    }


async def _strategic_latest(db: AsyncSession, mid: str) -> dict:
    """Pull the most recent trust + fraud scores from the insights table."""
    try:
        from app.models.strategic_insight import StrategicInsight
        trust_r = await db.execute(
            select(StrategicInsight)
            .where(StrategicInsight.merchant_id == mid, StrategicInsight.agent_name == "trust_graph")
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        fraud_r = await db.execute(
            select(StrategicInsight)
            .where(StrategicInsight.merchant_id == mid, StrategicInsight.agent_name == "fraud_sentinel")
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        growth_r = await db.execute(
            select(StrategicInsight)
            .where(StrategicInsight.merchant_id == mid, StrategicInsight.agent_name == "growth_coach")
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        trust_row  = trust_r.scalar_one_or_none()
        fraud_row  = fraud_r.scalar_one_or_none()
        growth_row = growth_r.scalar_one_or_none()
        return {
            "trust_score":   trust_row.score  if trust_row  else None,
            "fraud_score":   fraud_row.score  if fraud_row  else None,
            "growth_score":  growth_row.score if growth_row else None,
            "trust_flags":   (trust_row.payload  or {}).get("risk_flags",    []) if trust_row  else [],
            "fraud_alerts":  (fraud_row.payload  or {}).get("alert_reasons", []) if fraud_row  else [],
            "growth_trend":  (growth_row.payload or {}).get("trend_direction", "STABLE") if growth_row else "STABLE",
        }
    except Exception:
        return {"trust_score": None, "fraud_score": None, "growth_score": None,
                "trust_flags": [], "fraud_alerts": [], "growth_trend": "STABLE"}


# ── Follow-up / context memory helpers ────────────────────────

_FOLLOWUP_SIGNALS_BN: frozenset[str] = frozenset({
    "আরো", "আরও", "বিস্তারিত", "আরেকটু", "আবার", "সেটা", "এটা", "ওটা", "কোনটা",
})
_FOLLOWUP_SIGNALS_EN: frozenset[str] = frozenset({
    "more", "details", "again", "elaborate", "which", "explain", "tell",
})


def _is_followup(message: str) -> bool:
    """True when the message is a vague follow-up to the previous turn."""
    tokens = set(message.lower().strip().split())
    if len(tokens) > 6:
        return False
    return bool(tokens & _FOLLOWUP_SIGNALS_BN) or bool(tokens & _FOLLOWUP_SIGNALS_EN)


def _last_human_intent(history: list[dict]) -> str | None:
    """Scan history backwards and return the intent of the most recent user message."""
    for entry in reversed(history):
        if entry.get("role") == "user":
            content = entry.get("content", "")
            if content:
                result = detect_intent(content)
                if result.intent not in ("unknown",):
                    return result.intent
    return None


# ── Trend calculation (numpy if available, fallback otherwise) ──

def _calc_trend(values: list[float]) -> str:
    """'growing' | 'declining' | 'stable'  using linear regression slope."""
    if len(values) < 3:
        return "stable"
    if _HAS_NUMPY:
        import numpy as np  # noqa: PLC0415
        x = np.arange(len(values), dtype=float)
        y = np.array(values, dtype=float)
        if y.mean() == 0:
            return "stable"
        slope = float(np.polyfit(x, y, 1)[0])
        rel = slope / y.mean()
    else:
        # Simple linear regression without numpy
        n = len(values)
        mean_x = (n - 1) / 2
        mean_y = sum(values) / n
        num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
        den = sum((i - mean_x) ** 2 for i in range(n))
        slope = num / den if den else 0.0
        rel = slope / mean_y if mean_y else 0.0
    if rel > 0.05:
        return "growing"
    if rel < -0.05:
        return "declining"
    return "stable"


def _trend_emoji(trend: str, lang: str) -> str:
    if lang == "bn":
        return {"growing": "📈 বৃদ্ধি পাচ্ছে", "declining": "📉 কমছে", "stable": "➡️ স্থিতিশীল"}[trend]
    return {"growing": "📈 Growing", "declining": "📉 Declining", "stable": "➡️ Stable"}[trend]


# ── Individual response builders ───────────────────────────

async def _greet(merchant: Merchant, lang: str) -> str:
    if lang == "bn":
        return (
            f"আস্-সালামু আলাইকুম! আমি **SellerMate AI** 🤖\n\n"
            f"**{merchant.business_name}** এ আপনাকে স্বাগতম!\n\n"
            f"আমি ডাটাবেজ থেকে সরাসরি রিয়েল ডেটা দিয়ে উত্তর দিই:\n\n"
            f"- 📦 কম স্টক / ইনভেন্টরি\n"
            f"- 🛒 অর্ডার ও রাজস্ব রিপোর্ট\n"
            f"- 🏆 শীর্ষ পণ্য ও গ্রাহক\n"
            f"- 📊 ব্যবসার প্রবৃদ্ধি বিশ্লেষণ\n"
            f"- 🛡️ ট্রাস্ট ও ফ্রড স্কোর\n\n"
            f"কী জানতে চান?"
        )
    return (
        f"Hello! I'm **SellerMate AI** 🤖\n\n"
        f"Welcome to **{merchant.business_name}**!\n\n"
        f"I answer with real data directly from your database:\n\n"
        f"- 📦 Low stock / inventory alerts\n"
        f"- 🛒 Orders & revenue reports\n"
        f"- 🏆 Top products & customers\n"
        f"- 📊 Business growth analysis\n"
        f"- 🛡️ Trust & fraud scores\n\n"
        f"What would you like to know?"
    )


async def _today(db: AsyncSession, merchant: Merchant, lang: str) -> str:
    today  = await _today_stats(db, str(merchant.id))
    inv    = await _inventory_alerts(db, str(merchant.id))
    if lang == "bn":
        parts = [f"## 📊 আজকের সারাংশ — {merchant.business_name}\n"]
        parts += [
            f"- 🛒 অর্ডার: **{today['count']}টি**",
            f"- 💰 রাজস্ব: **{_fmt(today['revenue'])}**",
            f"- ⏳ পেন্ডিং: **{today['pending']}টি**",
        ]
        if inv["out"]:  parts.append(f"- 🔴 স্টকশূন্য: **{inv['out']}টি ভ্যারিয়েন্ট**")
        if inv["low"]:  parts.append(f"- 🟡 কম স্টক: **{inv['low']}টি ভ্যারিয়েন্ট**")
        if not inv["out"] and not inv["low"]: parts.append("- ✅ ইনভেন্টরি সুস্থ")
    else:
        parts = [f"## 📊 Today's Summary — {merchant.business_name}\n"]
        parts += [
            f"- 🛒 Orders: **{today['count']}**",
            f"- 💰 Revenue: **{_fmt(today['revenue'])}**",
            f"- ⏳ Pending: **{today['pending']}**",
        ]
        if inv["out"]:  parts.append(f"- 🔴 Out of stock: **{inv['out']} variants**")
        if inv["low"]:  parts.append(f"- 🟡 Low stock: **{inv['low']} variants**")
        if not inv["out"] and not inv["low"]: parts.append("- ✅ Inventory healthy")
    return "\n".join(parts)


async def _stock(db: AsyncSession, mid: str, lang: str) -> str:
    inv   = await _inventory_alerts(db, mid)
    items = await _low_stock_items(db, mid)
    if not inv["out"] and not inv["low"]:
        return "✅ সব পণ্যের স্টক পর্যাপ্ত।" if lang == "bn" else "✅ All products are adequately stocked."
    if lang == "bn":
        parts = ["## 📦 স্টক সতর্কতা\n"]
        if inv["out"]: parts.append(f"🔴 **স্টকশূন্য**: {inv['out']}টি ভ্যারিয়েন্ট")
        if inv["low"]: parts.append(f"🟡 **কম স্টক**: {inv['low']}টি ভ্যারিয়েন্ট")
        if items:
            parts.append("\n**বিস্তারিত:**")
            for item in items:
                lbl = "শেষ" if item["qty"] == 0 else f"{item['qty']}টি বাকি"
                parts.append(f"- {item['name']}: {lbl}")
        parts.append("\n💡 দ্রুত রিস্টক করুন যাতে বিক্রয় না হারান।")
    else:
        parts = ["## 📦 Stock Alerts\n"]
        if inv["out"]: parts.append(f"🔴 **Out of stock**: {inv['out']} variants")
        if inv["low"]: parts.append(f"🟡 **Low stock**: {inv['low']} variants")
        if items:
            parts.append("\n**Details:**")
            for item in items:
                lbl = "out of stock" if item["qty"] == 0 else f"{item['qty']} remaining"
                parts.append(f"- {item['name']}: {lbl}")
        parts.append("\n💡 Restock urgently to avoid lost sales.")
    return "\n".join(parts)


async def _revenue(db: AsyncSession, mid: str, lang: str, days: int) -> str:
    stats = await _order_stats(db, mid, days)
    daily = await _daily_revenue(db, mid, days)
    trend = _calc_trend(daily)
    if lang == "bn":
        parts = [f"## 📊 রাজস্ব বিশ্লেষণ — শেষ {days} দিন\n"]
        parts += [
            f"- 💰 মোট রাজস্ব: **{_fmt(stats['revenue'])}**",
            f"- 🛒 মোট অর্ডার: **{stats['total']}টি**",
        ]
        if stats["total"]:
            parts.append(f"- 📦 গড় অর্ডার মূল্য: **{_fmt(stats['avg_value'])}**")
        parts.append(f"- 📈 রাজস্ব প্রবণতা: **{_trend_emoji(trend, 'bn')}**")
        if trend == "growing":
            parts.append("\n✅ রাজস্ব বাড়ছে — চমৎকার পারফরম্যান্স!")
        elif trend == "declining":
            parts.append("\n⚠️ রাজস্ব কমছে — নতুন অফার বা মার্কেটিং বিবেচনা করুন।")
    else:
        parts = [f"## 📊 Revenue Analysis — Last {days} days\n"]
        parts += [
            f"- 💰 Total revenue: **{_fmt(stats['revenue'])}**",
            f"- 🛒 Total orders: **{stats['total']}**",
        ]
        if stats["total"]:
            parts.append(f"- 📦 Avg order value: **{_fmt(stats['avg_value'])}**")
        parts.append(f"- 📈 Revenue trend: **{_trend_emoji(trend, 'en')}**")
        if trend == "growing":
            parts.append("\n✅ Revenue is growing — excellent performance!")
        elif trend == "declining":
            parts.append("\n⚠️ Revenue declining — consider promotions or marketing.")
    return "\n".join(parts)


async def _orders(db: AsyncSession, mid: str, lang: str, days: int) -> str:
    stats = await _order_stats(db, mid, days)
    if lang == "bn":
        parts = [f"## 🛒 অর্ডার রিপোর্ট — শেষ {days} দিন\n"]
        parts += [
            f"- মোট অর্ডার: **{stats['total']}টি**",
            f"- মোট রাজস্ব: **{_fmt(stats['revenue'])}**",
        ]
        labels = {"DELIVERED": "✅ ডেলিভার্ড", "PENDING": "⏳ পেন্ডিং",
                  "CANCELLED": "❌ বাতিল", "RETURNED": "🔄 ফেরত"}
    else:
        parts = [f"## 🛒 Order Report — Last {days} days\n"]
        parts += [
            f"- Total orders: **{stats['total']}**",
            f"- Total revenue: **{_fmt(stats['revenue'])}**",
        ]
        labels = {"DELIVERED": "✅ Delivered", "PENDING": "⏳ Pending",
                  "CANCELLED": "❌ Cancelled", "RETURNED": "🔄 Returned"}
    for key, lbl in labels.items():
        cnt = stats["status"].get(key, 0)
        if cnt:
            parts.append(f"- {lbl}: **{cnt}{'টি' if lang == 'bn' else ''}**")
    if stats["total"] > 0:
        cr = stats["status"].get("CANCELLED", 0) / stats["total"]
        if cr > 0.2:
            warn = (f"\n⚠️ বাতিলের হার **{cr:.0%}** — উদ্বেগজনক। কারণ অনুসন্ধান করুন।"
                    if lang == "bn"
                    else f"\n⚠️ Cancellation rate **{cr:.0%}** is high — investigate causes.")
            parts.append(warn)
    return "\n".join(parts)


async def _top_products_response(db: AsyncSession, mid: str, lang: str) -> str:
    products = await _top_products(db, mid, days=30, limit=5)
    if not products:
        return ("এখনো কোনো ডেলিভার্ড অর্ডার নেই।"
                if lang == "bn" else "No delivered orders yet.")
    if lang == "bn":
        parts = ["## 🏆 শীর্ষ বিক্রিত পণ্য (গত ৩০ দিন)\n"]
        for i, p in enumerate(products, 1):
            parts.append(f"{i}. **{p['name']}** — {p['units']}টি বিক্রিত · {_fmt(p['revenue'])}")
    else:
        parts = ["## 🏆 Top Selling Products (Last 30 days)\n"]
        for i, p in enumerate(products, 1):
            parts.append(f"{i}. **{p['name']}** — {p['units']} units · {_fmt(p['revenue'])}")
    return "\n".join(parts)


async def _customers(db: AsyncSession, mid: str, lang: str) -> str:
    cust = await _customer_stats(db, mid)
    total, repeat = cust["total"], cust["repeat"]
    retention = repeat / total if total else 0.0
    if lang == "bn":
        parts = [
            "## 👥 গ্রাহক বিশ্লেষণ\n",
            f"- মোট গ্রাহক: **{total}জন**",
            f"- নিয়মিত গ্রাহক (২+ অর্ডার): **{repeat}জন**",
            f"- রিটেনশন রেট: **{retention:.0%}**",
        ]
        if cust["top"]:
            parts.append("\n**শীর্ষ গ্রাহক:**")
            for i, c in enumerate(cust["top"], 1):
                parts.append(f"{i}. **{c['name']}** — {_fmt(c['spent'])} ({c['orders']} অর্ডার)")
        parts.append("\n✅ রিটেনশন চমৎকার!" if retention >= 0.3
                     else "\n💡 অফার পাঠিয়ে পুরনো গ্রাহকদের ফিরিয়ে আনুন।")
    else:
        parts = [
            "## 👥 Customer Analytics\n",
            f"- Total customers: **{total}**",
            f"- Repeat customers (2+ orders): **{repeat}**",
            f"- Retention rate: **{retention:.0%}**",
        ]
        if cust["top"]:
            parts.append("\n**Top customers:**")
            for i, c in enumerate(cust["top"], 1):
                parts.append(f"{i}. **{c['name']}** — {_fmt(c['spent'])} ({c['orders']} orders)")
        parts.append("\n✅ Excellent retention!" if retention >= 0.3
                     else "\n💡 Send special offers to bring back past customers.")
    return "\n".join(parts)


async def _strategic(db: AsyncSession, mid: str, lang: str, intent: str) -> str:
    data = await _strategic_latest(db, mid)

    def _no_data(msg_bn: str, msg_en: str) -> str:
        return msg_bn if lang == "bn" else msg_en

    if intent == "trust_score":
        ts = data.get("trust_score")
        if ts is None:
            return _no_data(
                "ট্রাস্ট স্কোর নেই। এআই সেন্টারে গিয়ে এজেন্ট চালান।",
                "No trust score yet. Go to AI Center and run the agents.",
            )
        flags = data.get("trust_flags", [])
        if lang == "bn":
            parts = [f"## 📈 ট্রাস্ট স্কোর: **{ts}/100**\n"]
            parts.append("✅ বিশ্বাসযোগ্যতা উচ্চ।" if ts >= 75
                         else "🟡 মাঝারি — উন্নতির সুযোগ আছে।" if ts >= 50
                         else "🔴 স্কোর কম — দ্রুত পদক্ষেপ নিন।")
            if flags: parts.append(f"\n⚠️ ঝুঁকি: {', '.join(flags[:3])}")
        else:
            parts = [f"## 📈 Trust Score: **{ts}/100**\n"]
            parts.append("✅ Business credibility is high." if ts >= 75
                         else "🟡 Moderate — room for improvement." if ts >= 50
                         else "🔴 Low — take immediate action.")
            if flags: parts.append(f"\n⚠️ Risk flags: {', '.join(flags[:3])}")
        return "\n".join(parts)

    if intent == "fraud_risk":
        fs = data.get("fraud_score")
        if fs is None:
            return _no_data(
                "ফ্রড রিপোর্ট নেই। এআই সেন্টারে গিয়ে এজেন্ট চালান।",
                "No fraud report yet. Go to AI Center and run the agents.",
            )
        alerts = data.get("fraud_alerts", [])
        if lang == "bn":
            parts = [f"## 🚨 ফ্রড ঝুঁকি: **{fs}/100**\n"]
            parts.append("✅ ঝুঁকি কম।" if fs <= 20
                         else "🟡 মাঝারি ঝুঁকি — সতর্ক থাকুন।" if fs <= 50
                         else "🔴 উচ্চ ঝুঁকি — তাৎক্ষণিক পদক্ষেপ নিন।")
            if alerts: parts.append(f"\n⚠️ {alerts[0].split(':')[0]}")
        else:
            parts = [f"## 🚨 Fraud Risk: **{fs}/100**\n"]
            parts.append("✅ Risk is low." if fs <= 20
                         else "🟡 Moderate — stay vigilant." if fs <= 50
                         else "🔴 High risk — take immediate action.")
            if alerts: parts.append(f"\n⚠️ {alerts[0].split(':')[0]}")
        return "\n".join(parts)

    # Generic strategic summary
    ts = data.get("trust_score")
    fs = data.get("fraud_score")
    gs = data.get("growth_score")
    if ts is None and fs is None:
        return _no_data(
            "এআই সেন্টারে গিয়ে প্রথমে এজেন্ট চালান।",
            "Run agents in AI Center first to generate scores.",
        )
    if lang == "bn":
        return (
            f"## 🛡️ এআই স্কোর সারাংশ\n\n"
            f"- ট্রাস্ট স্কোর: **{ts if ts is not None else 'N/A'}/100**\n"
            f"- ফ্রড ঝুঁকি: **{fs if fs is not None else 'N/A'}/100**\n"
            + (f"- প্রবৃদ্ধি স্কোর: **{gs}/100**\n" if gs is not None else "")
            + "\nবিস্তারিতের জন্য **এআই সেন্টার** পেজে যান।"
        )
    return (
        f"## 🛡️ AI Score Summary\n\n"
        f"- Trust Score: **{ts if ts is not None else 'N/A'}/100**\n"
        f"- Fraud Risk: **{fs if fs is not None else 'N/A'}/100**\n"
        + (f"- Growth Score: **{gs}/100**\n" if gs is not None else "")
        + "\nFor full analysis visit the **AI Center** page."
    )


async def _restock(db: AsyncSession, mid: str, lang: str) -> str:
    items = await _low_stock_items(db, mid, limit=7)
    top   = await _top_products(db, mid, days=30, limit=3)
    if lang == "bn":
        parts = ["## 📦 রিস্টক পরামর্শ\n"]
        if items:
            parts.append("**অবিলম্বে রিস্টক করুন:**")
            for item in items:
                urgency = "🔴 জরুরি" if item["qty"] == 0 else "🟡 শীঘ্রই"
                parts.append(f"- {item['name']}: {urgency} (স্টক: {item['qty']})")
        if top:
            parts.append("\n**বেশি বিক্রয়ের পণ্য (প্রাধান্য দিন):**")
            for p in top:
                parts.append(f"- {p['name']}: {p['units']}টি বিক্রিত (৩০ দিনে)")
        if not items and not top:
            parts.append("সব পণ্যের স্টক পর্যাপ্ত।")
    else:
        parts = ["## 📦 Restock Advice\n"]
        if items:
            parts.append("**Restock immediately:**")
            for item in items:
                urgency = "🔴 Urgent" if item["qty"] == 0 else "🟡 Soon"
                parts.append(f"- {item['name']}: {urgency} (stock: {item['qty']})")
        if top:
            parts.append("\n**High-velocity products (prioritize):**")
            for p in top:
                parts.append(f"- {p['name']}: {p['units']} units sold (30 days)")
        if not items and not top:
            parts.append("All products are adequately stocked.")
    return "\n".join(parts)


async def _growth(db: AsyncSession, mid: str, lang: str) -> str:
    now  = datetime.now(timezone.utc)
    since_30 = now - timedelta(days=30)
    since_60 = now - timedelta(days=60)

    rev_30_r = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.merchant_id == mid, Order.created_at >= since_30
        )
    )
    rev_60_r = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.merchant_id == mid,
            Order.created_at >= since_60,
            Order.created_at < since_30,
        )
    )
    rev_30 = float(rev_30_r.scalar_one() or 0)
    rev_prev = float(rev_60_r.scalar_one() or 0)
    growth_pct = (rev_30 - rev_prev) / rev_prev * 100 if rev_prev > 0 else 0.0

    daily  = await _daily_revenue(db, mid, days=30)
    trend  = _calc_trend(daily)
    cust   = await _customer_stats(db, mid)
    top    = await _top_products(db, mid, days=30, limit=1)
    retention = cust["repeat"] / cust["total"] if cust["total"] else 0.0

    if lang == "bn":
        arrow  = "📈" if growth_pct >= 0 else "📉"
        parts  = ["## 💡 প্রবৃদ্ধি বিশ্লেষণ ও পরামর্শ\n"]
        parts += [
            f"- গত ৩০ দিনের রাজস্ব: **{_fmt(rev_30)}**",
        ]
        if rev_prev:
            parts.append(f"- আগের ৩০ দিনের তুলনায়: {arrow} **{abs(growth_pct):.0f}%"
                         f"{'বৃদ্ধি' if growth_pct >= 0 else 'হ্রাস'}**")
        parts += [
            f"- প্রবণতা: **{_trend_emoji(trend, 'bn')}**",
            f"- রিটেনশন রেট: **{retention:.0%}**",
            "",
            "**পরামর্শ:**",
        ]
        if trend == "declining" or growth_pct < -10:
            parts += ["- 📣 নতুন প্রমোশন চালু করুন", "- 💬 পুরনো গ্রাহকদের বিশেষ অফার পাঠান"]
        if retention < 0.25:
            parts.append("- 🎁 লয়্যালটি অফার দিয়ে গ্রাহক ধরে রাখুন")
        if top:
            parts.append(f"- 📦 **{top[0]['name']}** সবচেয়ে বেশি বিক্রি — স্টক নিশ্চিত রাখুন")
        if trend == "growing":
            parts.append("- ✅ ভালো পারফরম্যান্স — এই গতি বজায় রাখুন!")
    else:
        arrow = "📈" if growth_pct >= 0 else "📉"
        parts = ["## 💡 Growth Analysis & Advice\n"]
        parts += [f"- Last 30 days revenue: **{_fmt(rev_30)}**"]
        if rev_prev:
            parts.append(f"- vs. previous 30 days: {arrow} **{abs(growth_pct):.0f}% "
                         f"{'growth' if growth_pct >= 0 else 'decline'}**")
        parts += [
            f"- Trend: **{_trend_emoji(trend, 'en')}**",
            f"- Retention rate: **{retention:.0%}**",
            "",
            "**Recommendations:**",
        ]
        if trend == "declining" or growth_pct < -10:
            parts += ["- 📣 Launch new promotions", "- 💬 Message past customers with special offers"]
        if retention < 0.25:
            parts.append("- 🎁 Add loyalty rewards to retain customers")
        if top:
            parts.append(f"- 📦 **{top[0]['name']}** is your #1 seller — keep it well stocked")
        if trend == "growing":
            parts.append("- ✅ Great performance — keep the momentum!")
    return "\n".join(parts)


async def _help_text(lang: str) -> str:
    if lang == "bn":
        return (
            "## 🤖 আমি যা করতে পারি\n\n"
            "- **আজকের সারাংশ** → 'আজকের অর্ডার কেমন?'\n"
            "- **স্টক চেক** → 'কম স্টক কোনটা?'\n"
            "- **শীর্ষ পণ্য** → 'কোন পণ্য সবচেয়ে বেশি বিক্রি?'\n"
            "- **রাজস্ব** → 'এই মাসে কত আয়?'\n"
            "- **অর্ডার** → 'গত ৩০ দিনের অর্ডার দেখাও'\n"
            "- **গ্রাহক** → 'শীর্ষ গ্রাহক কে?'\n"
            "- **ট্রাস্ট স্কোর** → 'আমার ট্রাস্ট স্কোর কত?'\n"
            "- **ফ্রড ঝুঁকি** → 'ফ্রড ঝুঁকি আছে কি?'\n"
            "- **রিস্টক পরামর্শ** → 'কী অর্ডার করা উচিত?'\n"
            "- **প্রবৃদ্ধি পরামর্শ** → 'ব্যবসা বাড়ানোর উপায় কী?'"
        )
    return (
        "## 🤖 What I Can Do\n\n"
        "- **Today's summary** → 'How are today's orders?'\n"
        "- **Stock check** → 'What's low on stock?'\n"
        "- **Top products** → 'Which product sells most?'\n"
        "- **Revenue** → 'How much did I earn this month?'\n"
        "- **Orders** → 'Show last 30 days orders'\n"
        "- **Customers** → 'Who is my best customer?'\n"
        "- **Trust score** → 'What is my trust score?'\n"
        "- **Fraud risk** → 'Is there any fraud risk?'\n"
        "- **Restock advice** → 'What should I reorder?'\n"
        "- **Growth advice** → 'How can I grow my business?'"
    )


# ── Main dispatcher ────────────────────────────────────────

async def generate_smart_response(
    merchant: Merchant,
    user_message: str,
    db: AsyncSession,
    history: list[dict] | None = None,
) -> str:
    result: IntentResult = detect_intent(user_message)
    intent = result.intent
    lang   = result.lang
    mid    = str(merchant.id)

    # Context memory: inherit last intent when user sends a vague follow-up
    if history and (intent == "unknown" or _is_followup(user_message)):
        prev_intent = _last_human_intent(history)
        if prev_intent:
            intent = prev_intent

    # Extract time-period hint from raw message
    msg_l = user_message.lower()
    days = 7  if any(w in msg_l for w in ["৭", "7", "সপ্তাহ", "week"])  else \
           90 if any(w in msg_l for w in ["৯০", "90", "তিন মাস", "quarter"]) else \
           30

    try:
        if   intent == "greeting":       return await _greet(merchant, lang)
        elif intent == "help":           return await _help_text(lang)
        elif intent == "today_summary":  return await _today(db, merchant, lang)
        elif intent == "low_stock":      return await _stock(db, mid, lang)
        elif intent == "top_products":   return await _top_products_response(db, mid, lang)
        elif intent == "revenue_summary":return await _revenue(db, mid, lang, days)
        elif intent == "order_summary":  return await _orders(db, mid, lang, days)
        elif intent == "best_customers": return await _customers(db, mid, lang)
        elif intent in ("trust_score", "fraud_risk"):
            return await _strategic(db, mid, lang, intent)
        elif intent == "restock_advice": return await _restock(db, mid, lang)
        elif intent == "growth_advice":  return await _growth(db, mid, lang)
        else:                            return await _today(db, merchant, lang)
    except Exception as exc:
        return (f"⚠️ ত্রুটি: {exc}" if lang == "bn" else f"⚠️ Error: {exc}")


async def stream_package_engine(
    merchant: Merchant,
    user_message: str,
    db: AsyncSession,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream the smart response in word-group chunks."""
    text = await generate_smart_response(merchant, user_message, db, history)
    words = text.split(" ")
    buf = ""
    for i, word in enumerate(words):
        buf += ("" if i == 0 else " ") + word
        if len(buf) >= 30 or i == len(words) - 1:
            yield buf
            buf = ""
            await asyncio.sleep(0.010)
