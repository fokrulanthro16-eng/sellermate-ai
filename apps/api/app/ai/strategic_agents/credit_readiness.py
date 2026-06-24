"""
CreditReadiness — estimates merchant eligibility for business credit / financing.

Signals measured over the past 90 days:
  - Revenue consistency (coefficient of variation on 3 monthly buckets)  +20
  - Revenue growth (positive MoM for 2+ consecutive months)              +15
  - Order volume maturity (>= 50 orders/month average)                   +15
  - Payment collection rate (paid / total)                               +15
  - Cancellation rate penalty (> 30% -> -15)                            -15
  - Customer diversity (top customer < 30% of revenue)                   +10
  - Inventory health (< 10% SKUs out-of-stock)                           +10

Score 0-100: ELIGIBLE >= 75, BORDERLINE 50-74, NOT_ELIGIBLE < 50
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.product import Product, ProductVariant

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


@dataclass
class CreditResult:
    credit_score: int
    eligibility: str                    # ELIGIBLE | BORDERLINE | NOT_ELIGIBLE
    revenue_consistency: float          # coefficient of variation (lower = better)
    payment_collection_rate: float
    cancellation_rate: float
    monthly_revenue_avg: float
    credit_limit_estimate: float
    improvement_tips: list[str] = field(default_factory=list)
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict = field(default_factory=dict)


def _cv(values: list[float]) -> float:
    if not values or all(v == 0 for v in values):
        return 0.0
    if _HAS_NUMPY:
        arr = np.array(values, dtype=float)
        mean = float(arr.mean())
        return float(arr.std() / mean) if mean else 0.0
    n = len(values)
    mean = sum(values) / n
    if mean == 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / n
    return (var ** 0.5) / mean


class CreditReadiness:
    """Estimates merchant credit-readiness for financing eligibility."""

    WINDOW_DAYS  = 90
    MONTHLY_DAYS = 30

    async def run(self, db: AsyncSession, merchant_id: str) -> CreditResult:
        now   = datetime.now(UTC)
        since = now - timedelta(days=self.WINDOW_DAYS)

        # ── Monthly revenue (M-2, M-1, M0) ──────────────────
        monthly_rev: list[float] = []
        for i in range(2, -1, -1):
            start = now - timedelta(days=(i + 1) * self.MONTHLY_DAYS)
            end   = now - timedelta(days=i * self.MONTHLY_DAYS)
            r = await db.execute(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.merchant_id == merchant_id,
                    Order.created_at  >= start,
                    Order.created_at  <  end,
                    Order.status      == OrderStatus.DELIVERED,
                )
            )
            monthly_rev.append(float(r.scalar_one()))

        monthly_avg = sum(monthly_rev) / 3
        rev_cv      = _cv(monthly_rev)

        # Consecutive positive MoM months
        consecutive_growth = 0
        for j in range(1, len(monthly_rev)):
            if monthly_rev[j] > monthly_rev[j - 1]:
                consecutive_growth += 1
            else:
                break

        # ── Order totals over 90-day window ──────────────────
        total_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at  >= since,
            )
        )
        total_orders     = int(total_r.scalar_one() or 0)
        monthly_order_avg = total_orders / 3.0

        paid_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at  >= since,
                Order.payment_status == PaymentStatus.PAID,
            )
        )
        paid_orders  = int(paid_r.scalar_one() or 0)
        payment_rate = paid_orders / total_orders if total_orders else 0.0

        cancel_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at  >= since,
                Order.status      == OrderStatus.CANCELLED,
            )
        )
        cancelled   = int(cancel_r.scalar_one() or 0)
        cancel_rate = cancelled / total_orders if total_orders else 0.0

        # ── Top-customer revenue share ────────────────────────
        top_r = await db.execute(
            select(Order.customer_id, func.sum(Order.total_amount).label("rev"))
            .where(
                Order.merchant_id == merchant_id,
                Order.created_at  >= since,
                Order.status      == OrderStatus.DELIVERED,
            )
            .group_by(Order.customer_id)
            .order_by(func.sum(Order.total_amount).desc())
            .limit(1)
        )
        top_row = top_r.first()
        total_rev         = sum(monthly_rev)
        top_cust_share    = (float(top_row.rev) / total_rev) if (top_row and total_rev) else 0.0

        # ── Inventory health: OOS rate (join through Product) ─
        sku_total_r = await db.execute(
            select(func.count(ProductVariant.id))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active   == True,
            )
        )
        sku_total = int(sku_total_r.scalar_one() or 0)

        sku_oos_r = await db.execute(
            select(func.count(ProductVariant.id))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                Product.merchant_id          == merchant_id,
                Product.is_active            == True,
                ProductVariant.stock_quantity == 0,
            )
        )
        sku_oos  = int(sku_oos_r.scalar_one() or 0)
        oos_rate = sku_oos / sku_total if sku_total else 0.0

        # ── Score ─────────────────────────────────────────────
        score: int = 0
        tips:  list[str] = []

        if rev_cv <= 0.15:         score += 20
        elif rev_cv <= 0.35:       score += 10
        else:                      tips.append("STABILIZE_REVENUE")

        if consecutive_growth >= 2: score += 15
        elif consecutive_growth == 1: score += 8
        else:                      tips.append("GROW_REVENUE")

        if monthly_order_avg >= 50: score += 15
        elif monthly_order_avg >= 20: score += 8
        else:                      tips.append("INCREASE_ORDER_VOLUME")

        if payment_rate >= 0.85:   score += 15
        elif payment_rate >= 0.65: score += 8
        else:                      tips.append("IMPROVE_PAYMENT_COLLECTION")

        if cancel_rate > 0.30:
            score -= 15
            tips.append("REDUCE_CANCELLATIONS")
        elif cancel_rate > 0.15:
            score -= 5

        if top_cust_share < 0.30:  score += 10
        elif top_cust_share < 0.50: score += 5
        else:                      tips.append("DIVERSIFY_CUSTOMER_BASE")

        if oos_rate < 0.10:        score += 10
        elif oos_rate < 0.25:      score += 5
        else:                      tips.append("RESTOCK_INVENTORY")

        score = max(0, min(100, score))

        eligibility = (
            "ELIGIBLE"     if score >= 75 else
            "BORDERLINE"   if score >= 50 else
            "NOT_ELIGIBLE"
        )

        multiplier     = 1.5 if score >= 75 else 1.0 if score >= 50 else 0.5
        credit_limit   = monthly_avg * multiplier

        if score >= 75:
            explanation_bn = (
                f"আপনার ব্যবসা ক্রেডিটের জন্য যোগ্য। মাসিক গড় রাজস্ব ৳{monthly_avg:,.0f}, "
                f"পেমেন্ট সংগ্রহ {payment_rate*100:.0f}%। আনুমানিক সীমা: ৳{credit_limit:,.0f}।"
            )
            explanation_en = (
                f"Your business qualifies for credit. Monthly avg revenue ৳{monthly_avg:,.0f}, "
                f"payment collection {payment_rate*100:.0f}%. Estimated limit: ৳{credit_limit:,.0f}."
            )
        elif score >= 50:
            explanation_bn = (
                f"সীমান্তরেখায় আছেন। কিছু উন্নতি করলে পূর্ণ যোগ্যতা পাবেন। "
                f"মাসিক গড় রাজস্ব ৳{monthly_avg:,.0f}।"
            )
            explanation_en = (
                f"Borderline eligibility. A few improvements unlock full qualification. "
                f"Monthly avg revenue ৳{monthly_avg:,.0f}."
            )
        else:
            explanation_bn = (
                f"এই মুহূর্তে যোগ্য নয়। নিচের পরামর্শ অনুসরণ করুন। "
                f"মাসিক গড় রাজস্ব ৳{monthly_avg:,.0f}।"
            )
            explanation_en = (
                f"Not eligible right now. Follow the improvement tips below. "
                f"Monthly avg revenue ৳{monthly_avg:,.0f}."
            )

        return CreditResult(
            credit_score=score,
            eligibility=eligibility,
            revenue_consistency=rev_cv,
            payment_collection_rate=payment_rate,
            cancellation_rate=cancel_rate,
            monthly_revenue_avg=monthly_avg,
            credit_limit_estimate=credit_limit,
            improvement_tips=tips,
            explanation_bn=explanation_bn,
            explanation_en=explanation_en,
            details={
                "monthly_revenues": monthly_rev,
                "monthly_order_avg": round(monthly_order_avg, 1),
                "consecutive_growth_months": consecutive_growth,
                "top_customer_revenue_share": round(top_cust_share, 3),
                "oos_rate": round(oos_rate, 3),
                "cancel_rate": round(cancel_rate, 3),
                "payment_collection_rate": round(payment_rate, 3),
            },
        )
