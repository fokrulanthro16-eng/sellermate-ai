"""
TrustGraph — merchant trust scoring agent.

Analyses order fulfilment, payment collection, and customer retention to
produce a trust score (0-100), confidence level, and a list of risk flags.
"""

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order, OrderStatus, PaymentStatus


@dataclass
class TrustResult:
    trust_score: int                    # 0-100
    confidence: str                     # LOW | MEDIUM | HIGH
    risk_flags: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class TrustGraph:
    """Rule-based trust scorer for a single merchant."""

    async def run(self, db: AsyncSession, merchant_id: str) -> TrustResult:
        # ── Order counts ────────────────────────────────────────────
        total_r = await db.execute(
            select(func.count(Order.id)).where(Order.merchant_id == merchant_id)
        )
        total_orders = int(total_r.scalar_one())

        delivered_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.status == OrderStatus.DELIVERED,
            )
        )
        delivered = int(delivered_r.scalar_one())

        cancelled_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.status == OrderStatus.CANCELLED,
            )
        )
        cancelled = int(cancelled_r.scalar_one())

        paid_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.payment_status == PaymentStatus.PAID,
            )
        )
        paid_orders = int(paid_r.scalar_one())

        # ── Customer counts ─────────────────────────────────────────
        total_cust_r = await db.execute(
            select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
        )
        total_customers = int(total_cust_r.scalar_one())

        repeat_cust_r = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.merchant_id == merchant_id,
                Customer.total_orders > 1,
            )
        )
        repeat_customers = int(repeat_cust_r.scalar_one())

        # ── Score calculation ────────────────────────────────────────
        active = total_orders - cancelled
        delivery_rate = delivered / active if active > 0 else 0.0
        payment_rate = paid_orders / total_orders if total_orders > 0 else 0.0
        retention_rate = repeat_customers / total_customers if total_customers > 0 else 0.0
        cancel_rate = cancelled / total_orders if total_orders > 0 else 0.0

        score = 50
        risk_flags: list[str] = []

        if delivery_rate >= 0.80:
            score += 20
        elif delivery_rate >= 0.50:
            score += 10
        else:
            risk_flags.append("LOW_DELIVERY_RATE")

        if payment_rate >= 0.70:
            score += 15
        elif payment_rate >= 0.40:
            score += 7
        else:
            risk_flags.append("LOW_PAYMENT_COLLECTION")

        if retention_rate >= 0.30:
            score += 15
        elif retention_rate >= 0.10:
            score += 7

        if cancel_rate > 0.40:
            score -= 25
            risk_flags.append("HIGH_CANCELLATION_RATE")
        elif cancel_rate > 0.20:
            score -= 10
            risk_flags.append("ELEVATED_CANCELLATION_RATE")

        score = max(0, min(100, score))

        if total_orders < 10:
            confidence = "LOW"
        elif total_orders < 50:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        return TrustResult(
            trust_score=score,
            confidence=confidence,
            risk_flags=risk_flags,
            details={
                "total_orders": total_orders,
                "delivered_orders": delivered,
                "cancelled_orders": cancelled,
                "paid_orders": paid_orders,
                "total_customers": total_customers,
                "repeat_customers": repeat_customers,
                "delivery_rate": round(delivery_rate, 3),
                "payment_rate": round(payment_rate, 3),
                "retention_rate": round(retention_rate, 3),
                "cancellation_rate": round(cancel_rate, 3),
            },
        )
