"""
Hermit Agent — silent background intelligence.

Watches merchant data, produces structured insights, never sends messages.
All analysis is pure SQL; no external LLM calls.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, delete, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.hermit import HermitInsight, InsightSeverity, InsightType
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductVariant


# ── public API ────────────────────────────────────────────────────────────────


async def run_analysis(db: AsyncSession, merchant_id: str) -> dict:
    """Clear stale insights and regenerate from fresh data."""
    now              = datetime.now(UTC)
    thirty_ago       = now - timedelta(days=30)
    seven_ago        = now - timedelta(days=7)
    today            = now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_week_start  = today - timedelta(days=today.weekday())   # Monday 00:00 UTC
    last_week_start  = this_week_start - timedelta(days=7)

    # Remove all previous insights for this merchant
    del_result = await db.execute(
        delete(HermitInsight).where(HermitInsight.merchant_id == merchant_id)
    )
    cleared = del_result.rowcount if del_result.rowcount >= 0 else 0

    insights: list[HermitInsight] = []
    insights += await _analyze_slow_moving(db, merchant_id, now, thirty_ago)
    insights += await _analyze_low_stock(db, merchant_id)
    insights += await _analyze_repeat_buyers(db, merchant_id, thirty_ago)
    insights += await _analyze_unusual_orders(db, merchant_id, today, seven_ago)

    weekly = await _generate_weekly_health(
        db, merchant_id, now, this_week_start, last_week_start
    )
    insights.append(weekly)

    for insight in insights:
        db.add(insight)
    await db.flush()

    breakdown: dict[str, int] = {}
    for i in insights:
        k = i.insight_type.value
        breakdown[k] = breakdown.get(k, 0) + 1

    return {
        "insights_generated": len(insights),
        "insights_cleared": cleared,
        "breakdown": breakdown,
        "run_at": now,
    }


async def get_insights(
    db: AsyncSession,
    merchant_id: str,
    insight_type: InsightType | None = None,
    severity: InsightSeverity | None = None,
    unread_only: bool = False,
) -> list[HermitInsight]:
    severity_rank = case(
        (HermitInsight.severity == InsightSeverity.CRITICAL, 1),
        (HermitInsight.severity == InsightSeverity.WARNING,  2),
        else_=3,
    )
    query = select(HermitInsight).where(HermitInsight.merchant_id == merchant_id)
    if insight_type:
        query = query.where(HermitInsight.insight_type == insight_type)
    if severity:
        query = query.where(HermitInsight.severity == severity)
    if unread_only:
        query = query.where(HermitInsight.is_read.is_(False))
    query = query.order_by(severity_rank, HermitInsight.generated_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_read(db: AsyncSession, merchant_id: str, insight_id: str) -> bool:
    result = await db.execute(
        select(HermitInsight).where(
            HermitInsight.id == insight_id,
            HermitInsight.merchant_id == merchant_id,
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        return False
    insight.is_read = True
    return True


# ── analyzers ─────────────────────────────────────────────────────────────────


async def _analyze_slow_moving(
    db: AsyncSession,
    merchant_id: str,
    now: datetime,
    thirty_ago: datetime,
) -> list[HermitInsight]:
    two_weeks_ago = now - timedelta(days=14)

    # Product IDs that received at least one non-cancelled order in last 30 days
    recent_q = (
        select(distinct(OrderItem.product_id))
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.merchant_id == merchant_id,
            Order.created_at >= thirty_ago,
            Order.status != OrderStatus.CANCELLED,
        )
    )

    result = await db.execute(
        select(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            Product.created_at <= two_weeks_ago,
            Product.id.notin_(recent_q),
        )
        .order_by(Product.created_at.asc())
        .limit(10)
    )
    products = result.scalars().all()

    return [
        HermitInsight(
            merchant_id=merchant_id,
            insight_type=InsightType.SLOW_MOVING_PRODUCT,
            severity=InsightSeverity.WARNING,
            title=f'Slow-moving product: "{p.name}"',
            body=(
                f'"{p.name}" has had no orders in the last 30 days. '
                f"Consider a promotion or price review. "
                f"Base price: {p.base_price} BDT."
            ),
            meta={
                "product_id":   p.id,
                "product_name": p.name,
                "base_price":   str(p.base_price),
                "category":     p.category,
                "days_without_order": 30,
            },
        )
        for p in products
    ]


async def _analyze_low_stock(
    db: AsyncSession,
    merchant_id: str,
) -> list[HermitInsight]:
    result = await db.execute(
        select(ProductVariant, Product.name.label("product_name"))
        .join(Product, Product.id == ProductVariant.product_id)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            ProductVariant.low_stock_alert > 0,
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .order_by(ProductVariant.stock_quantity.asc())
        .limit(20)
    )
    rows = result.all()

    insights = []
    for row in rows:
        v: ProductVariant = row[0]
        product_name: str = row[1]
        is_zero = v.stock_quantity == 0
        severity = InsightSeverity.CRITICAL if is_zero else InsightSeverity.WARNING
        status   = "completely out of stock" if is_zero else f"only {v.stock_quantity} unit(s) left"
        insights.append(
            HermitInsight(
                merchant_id=merchant_id,
                insight_type=InsightType.LOW_STOCK,
                severity=severity,
                title=f'{"Out of stock" if is_zero else "Low stock"}: "{product_name}" — {v.name}',
                body=(
                    f'Variant "{v.name}" of "{product_name}" is {status} '
                    f"(alert threshold: {v.low_stock_alert} units). "
                    f"Restock to avoid missed sales."
                ),
                meta={
                    "variant_id":      v.id,
                    "variant_name":    v.name,
                    "product_name":    product_name,
                    "stock_quantity":  v.stock_quantity,
                    "low_stock_alert": v.low_stock_alert,
                },
            )
        )
    return insights


async def _analyze_repeat_buyers(
    db: AsyncSession,
    merchant_id: str,
    thirty_ago: datetime,
) -> list[HermitInsight]:
    result = await db.execute(
        select(
            Customer.id,
            Customer.name,
            Customer.phone,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .where(
            Customer.merchant_id == merchant_id,
            Order.created_at >= thirty_ago,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(Customer.id, Customer.name, Customer.phone)
        .having(func.count(Order.id) >= 2)
        .order_by(func.count(Order.id).desc())
        .limit(5)
    )
    rows = result.all()

    return [
        HermitInsight(
            merchant_id=merchant_id,
            insight_type=InsightType.REPEAT_BUYER,
            severity=InsightSeverity.INFO,
            title=f"Loyal customer: {row.name}",
            body=(
                f"{row.name} placed {row.order_count} orders in the last 30 days, "
                f"spending BDT {float(row.total_spent):,.0f} total. "
                "Consider a loyalty discount or VIP tag to retain them."
            ),
            meta={
                "customer_id":    row.id,
                "customer_name":  row.name,
                "customer_phone": row.phone,
                "order_count":    row.order_count,
                "total_spent":    str(float(row.total_spent)),
            },
        )
        for row in rows
    ]


async def _analyze_unusual_orders(
    db: AsyncSession,
    merchant_id: str,
    today: datetime,
    seven_ago: datetime,
) -> list[HermitInsight]:
    today_r = await db.execute(
        select(func.count(Order.id)).where(
            Order.merchant_id == merchant_id,
            Order.created_at >= today,
        )
    )
    today_count: int = today_r.scalar_one()

    week_r = await db.execute(
        select(func.count(Order.id)).where(
            Order.merchant_id == merchant_id,
            Order.created_at >= seven_ago,
            Order.created_at < today,
        )
    )
    week_total: int = week_r.scalar_one()
    daily_avg = week_total / 7.0

    insights = []
    if daily_avg < 2:
        # Not enough baseline to flag anomalies
        return insights

    if today_count >= daily_avg * 2.0:
        insights.append(
            HermitInsight(
                merchant_id=merchant_id,
                insight_type=InsightType.UNUSUAL_ORDER_PATTERN,
                severity=InsightSeverity.INFO,
                title="Order spike today",
                body=(
                    f"You received {today_count} orders today vs your "
                    f"7-day daily average of {daily_avg:.1f}. "
                    "This may indicate a viral post or successful promotion. "
                    "Ensure stock and fulfilment capacity can handle the volume."
                ),
                meta={
                    "today_count": today_count,
                    "daily_avg":   round(daily_avg, 1),
                    "spike_ratio": round(today_count / daily_avg, 2),
                },
            )
        )
    elif today_count == 0 and daily_avg >= 3:
        insights.append(
            HermitInsight(
                merchant_id=merchant_id,
                insight_type=InsightType.UNUSUAL_ORDER_PATTERN,
                severity=InsightSeverity.WARNING,
                title="No orders today — unusually quiet",
                body=(
                    f"No orders recorded today while your 7-day daily average is "
                    f"{daily_avg:.1f} orders/day. "
                    "Check that your shop is accessible and promotions are active."
                ),
                meta={
                    "today_count": today_count,
                    "daily_avg":   round(daily_avg, 1),
                },
            )
        )

    return insights


async def _generate_weekly_health(
    db: AsyncSession,
    merchant_id: str,
    now: datetime,
    this_week_start: datetime,
    last_week_start: datetime,
) -> HermitInsight:
    this_week_end = this_week_start + timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=7)
    effective_end = min(this_week_end, now)

    async def _week_stats(from_dt: datetime, to_dt: datetime) -> tuple[float, int]:
        r = await db.execute(
            select(
                func.coalesce(func.sum(Order.total_amount), 0).label("rev"),
                func.count(Order.id).label("cnt"),
            ).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= from_dt,
                Order.created_at < to_dt,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        row = r.one()
        return float(row.rev), int(row.cnt)

    this_rev, this_orders = await _week_stats(this_week_start, effective_end)
    last_rev, last_orders = await _week_stats(last_week_start, last_week_end)

    new_cust_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= this_week_start,
            Customer.created_at < effective_end,
        )
    )
    new_customers: int = new_cust_r.scalar_one()

    def _pct(current: float, previous: float) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    rev_change = _pct(this_rev, last_rev)
    ord_change = _pct(float(this_orders), float(last_orders))

    # Determine severity from revenue trend
    if this_rev == 0 and last_rev == 0:
        severity = InsightSeverity.INFO
        verdict  = "No sales yet this week. Promote your products to get started."
    elif rev_change <= -25:
        severity = InsightSeverity.WARNING
        verdict  = f"Revenue dropped {abs(rev_change):.1f}% vs last week. Review pricing, stock, and promotions."
    elif rev_change >= 20:
        severity = InsightSeverity.INFO
        verdict  = f"Great week! Revenue is up {rev_change:.1f}%. Keep the momentum going."
    else:
        severity = InsightSeverity.INFO
        verdict  = "Business is stable this week."

    sign = lambda v: ("+" if v >= 0 else "") + f"{v:.1f}%"

    body = (
        f"Weekly Health — {this_week_start.strftime('%b %d')} to "
        f"{effective_end.strftime('%b %d, %Y')}\n\n"
        f"Revenue:       BDT {this_rev:>10,.0f}  ({sign(rev_change)} vs last week)\n"
        f"Orders:        {this_orders:>10}  ({sign(ord_change)} vs last week)\n"
        f"New customers: {new_customers:>10}\n\n"
        f"{verdict}"
    )

    return HermitInsight(
        merchant_id=merchant_id,
        insight_type=InsightType.WEEKLY_HEALTH,
        severity=severity,
        title="Weekly merchant health summary",
        body=body,
        meta={
            "this_week_revenue":    this_rev,
            "last_week_revenue":    last_rev,
            "this_week_orders":     this_orders,
            "last_week_orders":     last_orders,
            "new_customers":        new_customers,
            "revenue_change_pct":   rev_change,
            "orders_change_pct":    ord_change,
            "week_start":           this_week_start.isoformat(),
            "week_end":             effective_end.isoformat(),
        },
        expires_at=this_week_end,
    )
