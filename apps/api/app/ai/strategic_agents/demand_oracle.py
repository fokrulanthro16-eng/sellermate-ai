"""
DemandOracle — stock velocity and restock urgency predictor.

For each product variant it calculates:
  daily_velocity  = units delivered over last 30 days / 30
  days_until_out  = current_stock / daily_velocity

Items with days_until_out ≤ 3 are CRITICAL; ≤ 7 are HIGH.

Produces a restock_score 0–100 (lower = more urgent action needed).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductVariant


@dataclass
class DemandItem:
    product_name: str
    variant_name: str
    current_stock: int
    daily_velocity: float         # avg units sold / day (last 30 days)
    days_until_stockout: float | None   # None if no recent sales
    urgency: str                  # CRITICAL | HIGH | MEDIUM | LOW


@dataclass
class DemandResult:
    restock_score: int            # 0–100 (lower = more critical restocking needed)
    critical_count: int
    high_count: int
    total_sku_tracked: int
    critical_items: list[DemandItem] = field(default_factory=list)
    high_items: list[DemandItem] = field(default_factory=list)
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict = field(default_factory=dict)


class DemandOracle:
    """Predicts restock urgency based on real sales velocity."""

    VELOCITY_DAYS = 30

    async def run(self, db: AsyncSession, merchant_id: str) -> DemandResult:
        now   = datetime.now(UTC)
        since = now - timedelta(days=self.VELOCITY_DAYS)

        # ── All variants for this merchant ───────────────────
        variants_r = await db.execute(
            select(
                ProductVariant.id,
                ProductVariant.name.label("vname"),
                ProductVariant.stock_quantity,
                Product.name.label("pname"),
            )
            .join(Product, Product.id == ProductVariant.product_id)
            .where(Product.merchant_id == merchant_id)
            .order_by(ProductVariant.stock_quantity.asc())
        )
        variants = variants_r.all()

        if not variants:
            return DemandResult(
                restock_score=100,
                critical_count=0,
                high_count=0,
                total_sku_tracked=0,
                explanation_bn="কোনো পণ্য ভ্যারিয়েন্ট নেই।",
                explanation_en="No product variants found.",
                details={"restock_score": 100, "total_sku_tracked": 0,
                         "critical_count": 0, "high_count": 0,
                         "velocity_window_days": self.VELOCITY_DAYS,
                         "critical_items": [], "high_items": [],
                         "explanation_bn": "কোনো পণ্য ভ্যারিয়েন্ট নেই।",
                         "explanation_en": "No product variants found."},
            )

        # ── Sales velocity per variant ───────────────────────
        velocity_r = await db.execute(
            select(
                OrderItem.variant_id,
                func.sum(OrderItem.quantity).label("total_sold"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.merchant_id == merchant_id,
                Order.status == OrderStatus.DELIVERED,
                Order.created_at >= since,
            )
            .group_by(OrderItem.variant_id)
        )
        velocity_map: dict[str, float] = {
            str(r.variant_id): float(r.total_sold) / self.VELOCITY_DAYS
            for r in velocity_r.all()
            if r.variant_id
        }

        critical_items: list[DemandItem] = []
        high_items: list[DemandItem] = []

        for v in variants:
            vid      = str(v.id)
            stock    = int(v.stock_quantity)
            velocity = velocity_map.get(vid, 0.0)

            if velocity > 0:
                days_left: float | None = stock / velocity
            elif stock == 0:
                days_left = 0.0
            else:
                days_left = None  # no recent sales — can't predict

            if stock == 0 or (days_left is not None and days_left <= 3):
                urgency = "CRITICAL"
            elif days_left is not None and days_left <= 7:
                urgency = "HIGH"
            elif days_left is not None and days_left <= 14:
                urgency = "MEDIUM"
            else:
                urgency = "LOW"

            item = DemandItem(
                product_name=v.pname,
                variant_name=v.vname or v.pname,
                current_stock=stock,
                daily_velocity=round(velocity, 3),
                days_until_stockout=round(days_left, 1) if days_left is not None else None,
                urgency=urgency,
            )
            if urgency == "CRITICAL":
                critical_items.append(item)
            elif urgency == "HIGH":
                high_items.append(item)

        # ── Score ────────────────────────────────────────────
        total_sku = len(variants)
        score = max(0, 100 - min(100, len(critical_items) * 20 + len(high_items) * 10))

        # ── Explanations ─────────────────────────────────────
        if not critical_items and not high_items:
            explanation_bn = f"কোনো জরুরি রিস্টক প্রয়োজন নেই ({total_sku}টি SKU বিশ্লেষণ)।"
            explanation_en = f"No urgent restocking needed ({total_sku} SKUs analyzed)."
        elif critical_items:
            explanation_bn = f"{len(critical_items)}টি পণ্য জরুরিভাবে স্টকশূন্য বা ৩ দিনের মধ্যে শেষ।"
            explanation_en = f"{len(critical_items)} product(s) critically out of stock or stockout within 3 days."
        else:
            explanation_bn = f"{len(high_items)}টি পণ্য ৭ দিনের মধ্যে শেষ হবে — রিস্টক করুন।"
            explanation_en = f"{len(high_items)} product(s) will run out within 7 days — restock soon."

        def _item_to_dict(i: DemandItem) -> dict:
            return {
                "product":       i.product_name,
                "variant":       i.variant_name,
                "stock":         i.current_stock,
                "velocity_day":  i.daily_velocity,
                "days_left":     i.days_until_stockout,
                "urgency":       i.urgency,
            }

        details = {
            "restock_score":        score,
            "total_sku_tracked":    total_sku,
            "critical_count":       len(critical_items),
            "high_count":           len(high_items),
            "velocity_window_days": self.VELOCITY_DAYS,
            "critical_items":       [_item_to_dict(i) for i in critical_items[:10]],
            "high_items":           [_item_to_dict(i) for i in high_items[:10]],
            "explanation_bn":       explanation_bn,
            "explanation_en":       explanation_en,
        }
        return DemandResult(
            restock_score=score,
            critical_count=len(critical_items),
            high_count=len(high_items),
            total_sku_tracked=total_sku,
            critical_items=critical_items[:10],
            high_items=high_items[:10],
            explanation_bn=explanation_bn,
            explanation_en=explanation_en,
            details=details,
        )
