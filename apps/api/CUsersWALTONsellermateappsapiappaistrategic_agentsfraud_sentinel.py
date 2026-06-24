"""
FraudSentinel — fraud pattern detection agent.

Scans recent orders for anomalous patterns and emits a fraud risk score
(0-100) plus human-readable alert reasons.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentStatus


@dataclass
class FraudResult:
    fraud_risk_score: int               # 0-100 (higher = riskier)
    alert_reasons: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class FraudSentinel:
    """Rule-based fraud pattern scanner."""

    WINDOW_DAYS = 30

    async def run(self, db: AsyncSession, merchant_id: str) -> FraudResult:
        now = datetime.now(UTC)
        window_start = now - timedelta(days=self.WINDOW_DAYS)

        # ── Recent window totals ─────────────────────────────────────
        total_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= window_start,
            )
        )
        recent_total = int(total_r.scalar_one())

        canc_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= window_start,
                Order.status == OrderStatus.CANCELLED,
            )
        )
        recent_cancelled = int(canc_r.scalar_one())

        # ── Unpaid large orders (due_amount > 0, older than 7 days) ─
        stale_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= window_start,
                Order.created_at < now - timedelta(days=7),
                Order.payment_status == PaymentStatus.UNPAID,
            )
        )
        stale_unpaid = int(stale_r.scalar_one())

        # ── Single-day spike: orders created on busiest single day ───
        spike_r = await db.execute(
            select(func.count(Order.id).label("cnt"))
            .where(
                Order.merchant_id == merchant_id,
                Order.created_at >= window_start,
            )
            .group_by(func.date_trunc("day", Order.created_at))
            .order_by(func.count(Order.id).desc())
            .limit(1)
        )
        row = spike_r.fetchone()
        max_single_day = int(row[0]) if row else 0
        avg_daily = recent_total / self.WINDOW_DAYS if recent_total > 0 else 0.0
        spike_ratio = max_single_day / avg_daily if avg_daily > 0 else 0.0

        # ── Score calculation ────────────────────────────────────────
        score = 0
        alert_reasons: list[str] = []

        cancel_rate = recent_cancelled / recent_total if recent_total > 0 else 0.0
        if cancel_rate > 0.50:
            score += 40
            alert_reasons.append(
                f"CANCELLATION_SPIKE: {recent_cancelled}/{recent_total} orders cancelled ({cancel_rate:.0%})"
            )
        elif cancel_rate > 0.30:
            score += 20
            alert_reasons.append(
                f"HIGH_CANCELLATION_RATE: {cancel_rate:.0%} in last {self.WINDOW_DAYS}d"
            )

        if stale_unpaid >= 5:
            score += 25
            alert_reasons.append(
                f"STALE_UNPAID_ORDERS: {stale_unpaid} orders unpaid for 7+ days"
            )
        elif stale_unpaid >= 2:
            score += 10
            alert_reasons.append(f"UNPAID_ORDER_ACCUMULATION: {stale_unpaid} stale unpaid orders")

        if spike_ratio >= 5.0 and recent_total >= 10:
            score += 25
            alert_reasons.append(
                f"ORDER_SPIKE: {max_single_day} orders in one day vs {avg_daily:.1f} daily avg"
            )

        score = max(0, min(100, score))

        return FraudResult(
            fraud_risk_score=score,
            alert_reasons=alert_reasons,
            details={
                "window_days": self.WINDOW_DAYS,
                "recent_total_orders": recent_total,
                "recent_cancelled": recent_cancelled,
                "cancellation_rate": round(cancel_rate, 3),
                "stale_unpaid_orders": stale_unpaid,
                "max_single_day_orders": max_single_day,
                "avg_daily_orders": round(avg_daily, 2),
                "spike_ratio": round(spike_ratio, 2),
            },
        )
