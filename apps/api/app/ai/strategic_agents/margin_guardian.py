"""
MarginGuardian — payment risk and margin health analysis agent.

Analyses the last 30 days of orders to detect:
  - High COD exposure (cash-on-delivery return risk)
  - Elevated return / refund rate
  - Heavy discounting patterns
  - Outstanding unpaid exposure (total due_amount)

Produces a margin health score 0–100 (higher = healthier).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus


@dataclass
class MarginResult:
    margin_score: int                # 0–100  (higher = healthier margins)
    risk_level: str                  # LOW | MEDIUM | HIGH
    cod_ratio: float                 # COD fraction of total orders
    refund_rate: float               # returned orders fraction
    avg_discount_rate: float         # avg discount_amount / avg subtotal
    unpaid_exposure: float           # sum of due_amount on all UNPAID orders
    flags: list[str] = field(default_factory=list)
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict = field(default_factory=dict)


class MarginGuardian:
    """Payment risk and margin health scorer."""

    WINDOW_DAYS = 30

    async def run(self, db: AsyncSession, merchant_id: str) -> MarginResult:
        now   = datetime.now(UTC)
        since = now - timedelta(days=self.WINDOW_DAYS)

        # ── Total orders in window ───────────────────────────
        total_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since,
            )
        )
        total = int(total_r.scalar_one() or 0)

        # ── COD orders ───────────────────────────────────────
        cod_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since,
                Order.payment_method == PaymentMethod.COD,
            )
        )
        cod_count = int(cod_r.scalar_one() or 0)
        cod_ratio = cod_count / total if total > 0 else 0.0

        # ── Returned orders ──────────────────────────────────
        returned_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since,
                Order.status == OrderStatus.RETURNED,
            )
        )
        returned    = int(returned_r.scalar_one() or 0)
        refund_rate = returned / total if total > 0 else 0.0

        # ── Average discount rate ────────────────────────────
        disc_r = await db.execute(
            select(
                func.coalesce(func.avg(Order.discount_amount), 0).label("avg_disc"),
                func.coalesce(func.avg(Order.subtotal), 0).label("avg_sub"),
            ).where(Order.merchant_id == merchant_id, Order.created_at >= since)
        )
        disc_row = disc_r.one()
        avg_disc  = float(disc_row.avg_disc or 0)
        avg_sub   = float(disc_row.avg_sub  or 0)
        avg_discount_rate = avg_disc / avg_sub if avg_sub > 0 else 0.0

        # ── Unpaid exposure ──────────────────────────────────
        unpaid_r = await db.execute(
            select(func.coalesce(func.sum(Order.due_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.payment_status == PaymentStatus.UNPAID,
            )
        )
        unpaid_exposure = float(unpaid_r.scalar_one() or 0)

        # ── Scoring ──────────────────────────────────────────
        score = 70
        flags: list[str] = []

        if cod_ratio > 0.80:
            score -= 20
            flags.append("HIGH_COD_EXPOSURE")
        elif cod_ratio > 0.60:
            score -= 10
            flags.append("ELEVATED_COD_RATIO")

        if refund_rate > 0.15:
            score -= 20
            flags.append("HIGH_RETURN_RATE")
        elif refund_rate > 0.08:
            score -= 10
            flags.append("ELEVATED_RETURN_RATE")

        if avg_discount_rate > 0.20:
            score -= 10
            flags.append("HEAVY_DISCOUNTING")
        elif avg_discount_rate > 0.10:
            score -= 5

        if unpaid_exposure > 50_000:
            score -= 15
            flags.append("HIGH_UNPAID_EXPOSURE")
        elif unpaid_exposure > 20_000:
            score -= 8
            flags.append("MODERATE_UNPAID_EXPOSURE")

        score = max(0, min(100, score))

        if score >= 70:
            risk_level = "LOW"
        elif score >= 45:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # ── Explanations ─────────────────────────────────────
        if risk_level == "LOW":
            explanation_bn = f"মার্জিন স্বাস্থ্য ভালো ({score}/100)। পেমেন্ট ঝুঁকি নিয়ন্ত্রণে।"
            explanation_en = f"Margin health is good ({score}/100). Payment risk is under control."
        elif risk_level == "MEDIUM":
            explanation_bn = f"মার্জিন স্বাস্থ্য মাঝারি ({score}/100)। COD অনুপাত ও রিটার্ন রেট পর্যবেক্ষণ করুন।"
            explanation_en = f"Margin health is moderate ({score}/100). Monitor COD ratio and return rate."
        else:
            explanation_bn = f"মার্জিন ঝুঁকি বেশি ({score}/100)। প্রিপেইড পেমেন্ট বাড়ান এবং ছাড় কমান।"
            explanation_en = f"Margin risk is high ({score}/100). Increase prepaid orders and reduce discounts."

        details = {
            "margin_score":       score,
            "risk_level":         risk_level,
            "window_days":        self.WINDOW_DAYS,
            "total_orders":       total,
            "cod_count":          cod_count,
            "cod_ratio":          round(cod_ratio, 3),
            "returned_orders":    returned,
            "refund_rate":        round(refund_rate, 3),
            "avg_discount_rate":  round(avg_discount_rate, 3),
            "unpaid_exposure":    round(unpaid_exposure, 2),
            "flags":              flags,
            "explanation_bn":     explanation_bn,
            "explanation_en":     explanation_en,
        }
        return MarginResult(
            margin_score=score,
            risk_level=risk_level,
            cod_ratio=round(cod_ratio, 3),
            refund_rate=round(refund_rate, 3),
            avg_discount_rate=round(avg_discount_rate, 3),
            unpaid_exposure=round(unpaid_exposure, 2),
            flags=flags,
            explanation_bn=explanation_bn,
            explanation_en=explanation_en,
            details=details,
        )
