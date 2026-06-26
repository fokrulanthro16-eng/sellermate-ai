"""
AI Agent System — 5 lightweight operational agents.
Each agent reads real DB data and produces structured insights + actions.
No external AI key required; works 100% from DB queries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.core.dependencies import CurrentMerchant, DB
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product, ProductVariant

router = APIRouter(tags=["agents"])

AGENT_CATALOGUE = [
    {
        "id": "commerce",
        "name": "Commerce Agent",
        "name_bn": "কমার্স এজেন্ট",
        "description": "Revenue trends, order velocity, and pricing recommendations",
        "description_bn": "রাজস্ব ট্রেন্ড, অর্ডার গতি ও মূল্য নির্ধারণ পরামর্শ",
        "icon": "TrendingUp",
        "color": "indigo",
    },
    {
        "id": "inventory",
        "name": "Inventory Agent",
        "name_bn": "ইনভেন্টরি এজেন্ট",
        "description": "Stock level monitoring, low-stock alerts, restock suggestions",
        "description_bn": "স্টক পর্যবেক্ষণ, কম স্টক সতর্কতা ও রিস্টক পরামর্শ",
        "icon": "Package",
        "color": "amber",
    },
    {
        "id": "marketing",
        "name": "Marketing Agent",
        "name_bn": "মার্কেটিং এজেন্ট",
        "description": "Customer segments, win-back targets, campaign ideas",
        "description_bn": "গ্রাহক বিভাগ, পুনরুদ্ধার লক্ষ্যমাত্রা ও ক্যাম্পেইন পরামর্শ",
        "icon": "Megaphone",
        "color": "emerald",
    },
    {
        "id": "analytics",
        "name": "Analytics Agent",
        "name_bn": "বিশ্লেষণ এজেন্ট",
        "description": "Category performance, cancellation analysis, payment health",
        "description_bn": "ক্যাটাগরি কর্মক্ষমতা, বাতিল বিশ্লেষণ ও পেমেন্ট স্বাস্থ্য",
        "icon": "BarChart3",
        "color": "blue",
    },
    {
        "id": "support",
        "name": "Support Agent",
        "name_bn": "সাপোর্ট এজেন্ট",
        "description": "Onboarding checklist, setup guidance, next-step recommendations",
        "description_bn": "অনবোর্ডিং চেকলিস্ট, সেটআপ নির্দেশিকা ও পরবর্তী পদক্ষেপ",
        "icon": "LifeBuoy",
        "color": "violet",
    },
]


def _fmt(amount: float) -> str:
    return f"৳{amount:,.0f}"


def _insight(type_: str, title: str, value: str, detail: str, positive: bool = True, change: str = "") -> dict:
    return {"type": type_, "title": title, "value": value, "change": change, "detail": detail, "positive": positive}


def _action(label: str, href: str, priority: str = "medium") -> dict:
    return {"label": label, "href": href, "priority": priority}


# ── Commerce Agent ────────────────────────────────────────────────────────────

async def _run_commerce(db: Any, merchant_id: str, now: datetime) -> dict:
    week_ago  = now - timedelta(days=7)
    prev_week = now - timedelta(days=14)
    month_ago = now - timedelta(days=30)

    async def _revenue(since: datetime, before: datetime | None = None):
        q = select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
        ).where(Order.merchant_id == merchant_id, Order.created_at >= since)
        if before:
            q = q.where(Order.created_at < before)
        r = await db.execute(q)
        row = r.one()
        return int(row[0]), float(row[1])

    curr_cnt, curr_rev  = await _revenue(week_ago)
    prev_cnt, prev_rev  = await _revenue(prev_week, week_ago)
    _, month_rev        = await _revenue(month_ago)

    rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0
    ord_delta  = curr_cnt - prev_cnt

    due_r = await db.execute(
        select(func.coalesce(func.sum(Order.due_amount), 0)).where(
            Order.merchant_id == merchant_id,
            Order.payment_status == PaymentStatus.UNPAID,
        )
    )
    due_amount = float(due_r.scalar() or 0)

    top_cat_r = await db.execute(
        select(Product.category, func.sum(OrderItem.quantity).label("qty"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Product.merchant_id == merchant_id)
        .group_by(Product.category)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(1)
    )
    top_cat = top_cat_r.one_or_none()

    insights = [
        _insight("revenue", "This Week's Revenue", _fmt(curr_rev),
                 f"Previous week: {_fmt(prev_rev)}",
                 rev_growth >= 0, f"{rev_growth:+.1f}%"),
        _insight("orders", "Orders This Week", str(curr_cnt),
                 f"Previous 7 days: {prev_cnt} orders",
                 ord_delta >= 0, f"{ord_delta:+d} vs last week"),
        _insight("monthly", "30-Day Revenue", _fmt(month_rev),
                 "Cumulative last 30 days", True),
    ]

    if due_amount > 0:
        insights.append(_insight("warning", "Unpaid Orders Total", _fmt(due_amount),
                                 "Follow up to collect payment", False))
    if top_cat:
        cat_label = top_cat.category.replace("_", " ").title()
        insights.append(_insight("category", "Best-Selling Category", cat_label,
                                 f"{top_cat.qty} units — focus stock here", True))

    actions = []
    if due_amount > 500:
        actions.append(_action("Follow up on unpaid orders", "/orders?payment_status=UNPAID", "high"))
    if rev_growth < -15:
        actions.append(_action("Run a discount campaign", "/campaigns", "high"))
    else:
        actions.append(_action("View full analytics", "/analytics", "low"))
    actions.append(_action("Check order pipeline", "/orders", "medium"))

    return {"title": "Commerce Overview", "insights": insights, "actions": actions}


# ── Inventory Agent ───────────────────────────────────────────────────────────

async def _run_inventory(db: Any, merchant_id: str) -> dict:
    low_r = await db.execute(
        select(
            Product.name,
            ProductVariant.name.label("vname"),
            ProductVariant.stock_quantity,
            ProductVariant.low_stock_alert,
        )
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .where(
            Product.merchant_id == merchant_id,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .order_by(ProductVariant.stock_quantity.asc())
        .limit(20)
    )
    low_rows = low_r.all()

    out_cnt = sum(1 for r in low_rows if r.stock_quantity == 0)
    low_cnt = len(low_rows) - out_cnt

    total_variants_r = await db.execute(
        select(func.count(ProductVariant.id))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(Product.merchant_id == merchant_id)
    )
    total_variants = int(total_variants_r.scalar() or 0)

    total_stock_r = await db.execute(
        select(func.coalesce(func.sum(ProductVariant.stock_quantity), 0))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(Product.merchant_id == merchant_id)
    )
    total_stock = int(total_stock_r.scalar() or 0)

    insights = [
        _insight("stock_total", "Total Stock Units", str(total_stock),
                 f"Across {total_variants} variants", True),
        _insight("low_stock", "Low Stock Alerts", str(low_cnt),
                 "Variants at or below reorder threshold", low_cnt == 0),
        _insight("out_of_stock", "Out of Stock", str(out_cnt),
                 "Variants with zero units — losing sales", out_cnt == 0),
    ]

    if low_rows:
        top5 = low_rows[:5]
        detail_parts = []
        for r in top5:
            name = r.name + (f" — {r.vname}" if r.vname and r.vname != r.name else "")
            qty_label = "OUT" if r.stock_quantity == 0 else str(r.stock_quantity)
            detail_parts.append(f"{name}: {qty_label}")
        insights.append(_insight("items", "Critical Items",
                                 f"{len(low_rows)} variants",
                                 " | ".join(detail_parts), False))

    actions = []
    if out_cnt > 0:
        actions.append(_action("Restock out-of-stock products", "/inventory", "high"))
    if low_cnt > 0:
        actions.append(_action("Update low-stock thresholds", "/inventory", "medium"))
    actions.append(_action("View full inventory", "/inventory", "low"))

    return {"title": "Inventory Health", "insights": insights, "actions": actions}


# ── Marketing Agent ───────────────────────────────────────────────────────────

async def _run_marketing(db: Any, merchant_id: str, now: datetime) -> dict:
    thirty_ago = now - timedelta(days=30)

    total_r = await db.execute(
        select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
    )
    total_customers = int(total_r.scalar() or 0)

    repeat_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.total_orders >= 2,
        )
    )
    repeat_customers = int(repeat_r.scalar() or 0)

    winback_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.total_orders == 1,
        )
    )
    winback_targets = int(winback_r.scalar() or 0)

    new_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= thirty_ago,
        )
    )
    new_customers = int(new_r.scalar() or 0)

    top_spenders_r = await db.execute(
        select(Customer.name, Customer.total_spent, Customer.total_orders)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.total_spent.desc())
        .limit(3)
    )
    top_spenders = top_spenders_r.all()

    retention = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0

    insights = [
        _insight("customers", "Total Customers", str(total_customers),
                 f"{new_customers} new in last 30 days", True),
        _insight("retention", "Retention Rate", f"{retention:.0f}%",
                 f"{repeat_customers} customers made 2+ orders",
                 retention >= 25),
        _insight("winback", "Win-Back Targets", str(winback_targets),
                 "One-time buyers — send them a discount", winback_targets == 0),
    ]

    if top_spenders:
        names = ", ".join(r.name for r in top_spenders)
        insights.append(_insight("vip", "Top Spenders", str(len(top_spenders)),
                                 names, True))

    actions = []
    if winback_targets > 0:
        actions.append(_action("Create win-back campaign", "/campaigns", "high"))
    if retention < 25:
        actions.append(_action("Set up loyalty offers", "/campaigns", "medium"))
    actions.append(_action("View all customers", "/customers", "low"))

    return {"title": "Marketing Opportunities", "insights": insights, "actions": actions}


# ── Analytics Agent ───────────────────────────────────────────────────────────

async def _run_analytics(db: Any, merchant_id: str, now: datetime) -> dict:
    thirty_ago = now - timedelta(days=30)

    status_rows = await db.execute(
        select(Order.status, func.count(Order.id).label("cnt"))
        .where(Order.merchant_id == merchant_id, Order.created_at >= thirty_ago)
        .group_by(Order.status)
    )
    status_map: dict[str, int] = {r.status: r.cnt for r in status_rows.all()}
    total_orders = sum(status_map.values())

    cancel_cnt = status_map.get(OrderStatus.CANCELLED, 0)
    delivered_cnt = status_map.get(OrderStatus.DELIVERED, 0)
    pending_cnt = status_map.get(OrderStatus.PENDING, 0)

    cancel_rate = (cancel_cnt / total_orders * 100) if total_orders > 0 else 0.0
    fulfill_rate = (delivered_cnt / total_orders * 100) if total_orders > 0 else 0.0

    payment_rows = await db.execute(
        select(Order.payment_status, func.count(Order.id))
        .where(Order.merchant_id == merchant_id, Order.created_at >= thirty_ago)
        .group_by(Order.payment_status)
    )
    payment_map: dict[str, int] = {r[0]: r[1] for r in payment_rows.all()}
    paid_cnt   = payment_map.get(PaymentStatus.PAID, 0)
    unpaid_cnt = payment_map.get(PaymentStatus.UNPAID, 0)

    cat_rows = await db.execute(
        select(Product.category, func.sum(OrderItem.quantity).label("qty"),
               func.sum(OrderItem.total_price).label("rev"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Product.merchant_id == merchant_id, Order.created_at >= thirty_ago)
        .group_by(Product.category)
        .order_by(func.sum(OrderItem.total_price).desc())
        .limit(5)
    )
    top_cats = cat_rows.all()

    insights = [
        _insight("fulfillment", "Fulfillment Rate", f"{fulfill_rate:.0f}%",
                 f"{delivered_cnt} of {total_orders} orders delivered", fulfill_rate >= 70),
        _insight("cancellation", "Cancellation Rate", f"{cancel_rate:.0f}%",
                 f"{cancel_cnt} orders cancelled in 30 days", cancel_rate < 15),
        _insight("pending_orders", "Pending Orders", str(pending_cnt),
                 "Need confirmation or processing", pending_cnt == 0),
        _insight("payment_health", "Payment Collection",
                 f"{paid_cnt}/{total_orders}" if total_orders else "—",
                 f"{unpaid_cnt} unpaid orders outstanding",
                 unpaid_cnt == 0),
    ]

    if top_cats:
        cat_summary = " | ".join(
            f"{r.category.replace('_',' ').title()}: {_fmt(float(r.rev or 0))}"
            for r in top_cats[:3]
        )
        insights.append(_insight("top_categories", "Top Revenue Categories",
                                 str(len(top_cats)), cat_summary, True))

    actions = []
    if cancel_rate > 20:
        actions.append(_action("Investigate cancellation reasons", "/orders?status=CANCELLED", "high"))
    if unpaid_cnt > 5:
        actions.append(_action("Follow up on unpaid orders", "/orders?payment_status=UNPAID", "high"))
    if pending_cnt > 0:
        actions.append(_action("Process pending orders", "/orders?status=PENDING", "medium"))
    actions.append(_action("View full analytics", "/analytics", "low"))

    return {"title": "Business Analytics", "insights": insights, "actions": actions}


# ── Support Agent ─────────────────────────────────────────────────────────────

async def _run_support(db: Any, merchant_id: str, merchant: Merchant) -> dict:
    prod_cnt_r = await db.execute(
        select(func.count(Product.id)).where(
            Product.merchant_id == merchant_id,
            Product.is_published.is_(True),
        )
    )
    published_products = int(prod_cnt_r.scalar() or 0)

    order_cnt_r = await db.execute(
        select(func.count(Order.id)).where(Order.merchant_id == merchant_id)
    )
    total_orders = int(order_cnt_r.scalar() or 0)

    has_slug        = bool(merchant.store_slug)
    has_profile     = bool(merchant.owner_name and merchant.district)
    has_payment     = bool(merchant.whatsapp_phone)
    has_description = bool(merchant.store_description)
    onboarding_done = bool(merchant.onboarding_done)

    steps = [
        {"label": "Complete business profile", "done": has_profile, "href": "/settings"},
        {"label": "Finish onboarding wizard",  "done": onboarding_done, "href": "/onboarding"},
        {"label": "Set store URL (slug)",       "done": has_slug,    "href": "/store-builder"},
        {"label": "Add store description",      "done": has_description, "href": "/store-builder"},
        {"label": "Add WhatsApp number",        "done": has_payment, "href": "/settings"},
        {"label": "Publish at least 1 product", "done": published_products > 0, "href": "/products"},
        {"label": "Receive first order",        "done": total_orders > 0, "href": "/orders"},
    ]

    done_count = sum(1 for s in steps if s["done"])
    pct = round(done_count / len(steps) * 100)

    insights = [
        _insight("progress", "Setup Progress", f"{pct}%",
                 f"{done_count} of {len(steps)} steps complete", pct >= 70),
        _insight("products", "Published Products", str(published_products),
                 "Products visible to buyers", published_products > 0),
        _insight("orders", "Total Orders Received", str(total_orders),
                 "Your store is getting traction" if total_orders > 0 else "Share your store link to get first order",
                 total_orders > 0),
        _insight("store", "Public Store", merchant.store_slug or "Not set",
                 f"/store/{merchant.store_slug}" if has_slug else "Set a store URL to go live",
                 has_slug),
    ]

    pending_steps = [s for s in steps if not s["done"]]
    actions = []
    for step in pending_steps[:3]:
        actions.append(_action(step["label"], step["href"], "high" if len(actions) == 0 else "medium"))
    if has_slug:
        actions.append(_action("Preview your public store", f"/store/{merchant.store_slug}", "low"))

    return {
        "title": "Setup & Onboarding",
        "insights": insights,
        "actions": actions,
        "checklist": steps,
    }


# ── Router endpoints ──────────────────────────────────────────────────────────

@router.get("")
async def list_agents(merchant: CurrentMerchant) -> dict:
    return {"success": True, "data": AGENT_CATALOGUE}


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, merchant: CurrentMerchant, db: DB) -> dict:
    valid_ids = {a["id"] for a in AGENT_CATALOGUE}
    if agent_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")

    now = datetime.now(timezone.utc)
    mid = merchant.id

    if agent_id == "commerce":
        result = await _run_commerce(db, mid, now)
    elif agent_id == "inventory":
        result = await _run_inventory(db, mid)
    elif agent_id == "marketing":
        result = await _run_marketing(db, mid, now)
    elif agent_id == "analytics":
        result = await _run_analytics(db, mid, now)
    else:
        result = await _run_support(db, mid, merchant)

    return {
        "success": True,
        "data": {
            "agent": agent_id,
            "generated_at": now.isoformat(),
            **result,
        },
    }
