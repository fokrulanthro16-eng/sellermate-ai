"""
GrowthCoach — revenue trend and business growth analysis agent.

Uses numpy polyfit (linear regression) to measure revenue slope over 30 days,
then compares to the previous 30-day window for month-over-month growth %.
All metrics come from real DB queries — no invented numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


@dataclass
class GrowthResult:
    growth_score: int                    # 0–100  (higher = stronger growth)
    trend_direction: str                 # GROWING | STABLE | DECLINING
    revenue_growth_pct: float            # month-over-month %
    top_product_concentration: float     # fraction of revenue from #1 product
    retention_rate: float
    recommendations: list[str] = field(default_factory=list)
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict = field(default_factory=dict)


def _polyfit_slope(values: list[float]) -> float:
    """Return the linear regression slope. Zero if too few points."""
    if len(values) < 3:
        return 0.0
    if _HAS_NUMPY:
        x = np.arange(len(values), dtype=float)
        y = np.array(values, dtype=float)
        return float(np.polyfit(x, y, 1)[0])
    n = len(values)
    mean_x = (n - 1) / 2.0
    mean_y = sum(values) / n
    num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    den = sum((i - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0


class GrowthCoach:
    """Revenue trend and growth health scorer for a single merchant."""

    async def run(self, db: AsyncSession, merchant_id: str) -> GrowthResult:
        now = datetime.now(UTC)
        since_30 = now - timedelta(days=30)
        since_60 = now - timedelta(days=60)

        # ── Revenue: last 30 vs previous 30 ─────────────────
        rev_30_r = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since_30,
            )
        )
        rev_prev_r = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since_60,
                Order.created_at < since_30,
            )
        )
        rev_30   = float(rev_30_r.scalar_one() or 0)
        rev_prev = float(rev_prev_r.scalar_one() or 0)

        growth_pct = ((rev_30 - rev_prev) / rev_prev * 100) if rev_prev > 0 else (100.0 if rev_30 > 0 else 0.0)

        # ── Daily revenue points for slope ──────────────────
        # cast to Date avoids asyncpg parameterising the "day" literal separately in
        # SELECT vs GROUP BY which PostgreSQL rejects as a grouping error.
        day_col = cast(Order.created_at, Date)
        daily_r = await db.execute(
            select(
                day_col.label("day"),
                func.coalesce(func.sum(Order.total_amount), 0).label("rev"),
            )
            .where(Order.merchant_id == merchant_id, Order.created_at >= since_30)
            .group_by(day_col)
            .order_by(day_col)
        )
        daily_values = [float(r.rev) for r in daily_r.all()]
        mean_daily   = sum(daily_values) / len(daily_values) if daily_values else 0.0
        slope        = _polyfit_slope(daily_values)
        rel_slope    = slope / mean_daily if mean_daily > 0 else 0.0

        if rel_slope > 0.05:
            trend_direction = "GROWING"
        elif rel_slope < -0.05:
            trend_direction = "DECLINING"
        else:
            trend_direction = "STABLE"

        # ── Customer retention ───────────────────────────────
        total_cust_r = await db.execute(
            select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
        )
        repeat_cust_r = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.merchant_id == merchant_id,
                Customer.total_orders > 1,
            )
        )
        total_cust  = int(total_cust_r.scalar_one() or 0)
        repeat_cust = int(repeat_cust_r.scalar_one() or 0)
        retention   = repeat_cust / total_cust if total_cust > 0 else 0.0

        # ── Top-product revenue concentration ───────────────
        total_orders_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since_30,
            )
        )
        total_orders = int(total_orders_r.scalar_one() or 0)

        top_prod_r = await db.execute(
            select(func.sum(OrderItem.total_price).label("rev"))
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                Product.merchant_id == merchant_id,
                Order.created_at >= since_30,
                Order.status == OrderStatus.DELIVERED,
            )
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.total_price).desc())
            .limit(1)
        )
        top_row = top_prod_r.fetchone()
        top_rev = float(top_row[0]) if top_row else 0.0
        concentration = top_rev / rev_30 if rev_30 > 0 else 0.0

        # ── Scoring ──────────────────────────────────────────
        score = 50
        recommendations: list[str] = []

        if trend_direction == "GROWING":
            score += 20
        elif trend_direction == "DECLINING":
            score -= 15
            recommendations.append("LAUNCH_PROMOTIONS")

        if growth_pct > 20:
            score += 15
        elif growth_pct > 0:
            score += 8
        elif growth_pct < -10:
            score -= 10
            if "LAUNCH_PROMOTIONS" not in recommendations:
                recommendations.append("LAUNCH_PROMOTIONS")

        if retention >= 0.30:
            score += 15
        elif retention >= 0.15:
            score += 7
        else:
            score -= 5
            recommendations.append("IMPROVE_RETENTION")

        if concentration > 0.70:
            score -= 10
            recommendations.append("DIVERSIFY_PRODUCTS")
        elif concentration > 0.50:
            recommendations.append("EXPAND_PRODUCT_RANGE")

        if total_orders >= 50:
            score += 5

        score = max(0, min(100, score))

        # ── Explanations ─────────────────────────────────────
        if score >= 75:
            explanation_bn = f"আপনার ব্যবসা চমৎকারভাবে বাড়ছে ({score}/100)। প্রবণতা: {trend_direction}।"
            explanation_en = f"Your business is growing excellently ({score}/100). Trend: {trend_direction}."
        elif score >= 50:
            explanation_bn = f"ব্যবসা মাঝারি গতিতে ({score}/100)। প্রবণতা: {trend_direction}।"
            explanation_en = f"Business performing moderately ({score}/100). Trend: {trend_direction}."
        else:
            explanation_bn = f"ব্যবসার প্রবৃদ্ধি দুর্বল ({score}/100)। দ্রুত পদক্ষেপ নিন।"
            explanation_en = f"Business growth is weak ({score}/100). Take immediate action."

        details = {
            "growth_score":              score,
            "trend_direction":           trend_direction,
            "revenue_last_30d":          round(rev_30, 2),
            "revenue_prev_30d":          round(rev_prev, 2),
            "revenue_growth_pct":        round(growth_pct, 2),
            "retention_rate":            round(retention, 3),
            "top_product_concentration": round(concentration, 3),
            "total_orders_30d":          total_orders,
            "recommendations":           recommendations,
            "explanation_bn":            explanation_bn,
            "explanation_en":            explanation_en,
        }
        return GrowthResult(
            growth_score=score,
            trend_direction=trend_direction,
            revenue_growth_pct=round(growth_pct, 2),
            top_product_concentration=round(concentration, 3),
            retention_rate=round(retention, 3),
            recommendations=recommendations,
            explanation_bn=explanation_bn,
            explanation_en=explanation_en,
            details=details,
        )
