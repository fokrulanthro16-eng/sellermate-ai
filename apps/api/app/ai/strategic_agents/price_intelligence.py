"""
PriceIntelligence — merchant pricing analysis agent.

Analyses order discount patterns to assess whether prices are fair,
high (needs heavy discounting to sell), or data is insufficient.
"""

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, OrderStatus


@dataclass
class PriceResult:
    verdict: str                             # FAIR | MODERATE | HIGH_PRICING_RISK | INSUFFICIENT_DATA
    avg_discount_pct: float
    heavily_discounted_count: int
    total_products_analyzed: int
    recommendations: list[str] = field(default_factory=list)
    price_items: list[dict] = field(default_factory=list)
    explanation_bn: str = ""
    explanation_en: str = ""


class PriceIntelligence:
    """Rule-based price fairness checker using order data."""

    async def run(self, db: AsyncSession, merchant_id: str) -> PriceResult:
        # Aggregate discount vs subtotal across non-cancelled orders
        agg_r = await db.execute(
            select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.discount_amount), 0),
                func.coalesce(func.sum(Order.subtotal), 0),
            ).where(
                Order.merchant_id == merchant_id,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.RETURNED]),
            )
        )
        total_orders, total_discount, total_subtotal = agg_r.one()
        total_orders = int(total_orders)
        total_discount = float(total_discount)
        total_subtotal = float(total_subtotal)

        avg_discount_pct = total_discount / total_subtotal if total_subtotal > 0 else 0.0

        # Per-product: avg selling price and units sold
        prod_r = await db.execute(
            select(
                OrderItem.product_id,
                OrderItem.product_name,
                func.count(OrderItem.id).label("times_sold"),
                func.avg(OrderItem.unit_price).label("avg_price"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.merchant_id == merchant_id,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.RETURNED]),
            )
            .group_by(OrderItem.product_id, OrderItem.product_name)
            .order_by(func.count(OrderItem.id).desc())
            .limit(20)
        )
        products = prod_r.all()

        # Count heavily discounted orders (discount > 20% of subtotal) in Python
        disc_r = await db.execute(
            select(Order.discount_amount, Order.subtotal).where(
                Order.merchant_id == merchant_id,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.RETURNED]),
                Order.subtotal > 0,
            )
        )
        heavily_discounted_count = sum(
            1 for d, s in disc_r.all() if float(s) > 0 and float(d) / float(s) > 0.20
        )

        # Verdict
        if total_orders < 5:
            verdict = "INSUFFICIENT_DATA"
            explanation_bn = "পর্যাপ্ত ডেটা নেই। আরও অর্ডার প্রক্রিয়া হলে মূল্য বিশ্লেষণ করা যাবে।"
            explanation_en = "Not enough data yet. Complete more orders to enable price analysis."
            recommendations = ["Keep recording orders — price analysis needs at least 5 completed orders"]
        elif avg_discount_pct > 0.25:
            verdict = "HIGH_PRICING_RISK"
            explanation_bn = f"গড় ছাড়ের হার {avg_discount_pct:.0%} — তালিকামূল্য পর্যালোচনা করুন।"
            explanation_en = f"Avg discount rate {avg_discount_pct:.0%} — your list prices may be too high."
            recommendations = [
                "Lower base prices instead of offering large discounts to sell",
                "Consider bundling products to increase perceived value",
                "Test lower price points on slow-moving products",
            ]
        elif avg_discount_pct > 0.10:
            verdict = "MODERATE"
            explanation_bn = f"গড় ছাড়ের হার {avg_discount_pct:.0%} — মাঝারি পর্যায়ে আছে।"
            explanation_en = f"Avg discount rate {avg_discount_pct:.0%} — moderate. Can be improved."
            recommendations = [
                "Gradually reduce discount frequency for your top products",
                "Highlight product value to justify full price",
            ]
        else:
            verdict = "FAIR"
            explanation_bn = f"মূল্য নির্ধারণ ভালো দেখাচ্ছে। গড় ছাড় মাত্র {avg_discount_pct:.0%}।"
            explanation_en = f"Pricing looks fair. Avg discount is only {avg_discount_pct:.0%}."
            recommendations = [
                "Pricing strategy looks healthy — maintain consistency",
                "Monitor competitor prices quarterly to stay competitive",
            ]

        price_items = [
            {
                "product_name": str(p.product_name),
                "product_id": str(p.product_id),
                "times_sold": int(p.times_sold),
                "avg_selling_price": round(float(p.avg_price or 0), 2),
            }
            for p in products[:10]
        ]

        return PriceResult(
            verdict=verdict,
            avg_discount_pct=round(avg_discount_pct, 3),
            heavily_discounted_count=heavily_discounted_count,
            total_products_analyzed=len(products),
            recommendations=recommendations,
            price_items=price_items,
            explanation_bn=explanation_bn,
            explanation_en=explanation_en,
        )
