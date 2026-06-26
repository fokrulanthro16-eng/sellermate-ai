"""
CommerceEngine — deterministic analytics using real DB data.
All methods produce structured results; no LLM required for analytics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Date, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.models.product import Product, ProductVariant


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class PriceRecommendation:
    product_id: str
    product_name: str
    current_price: float
    recommended_price: float
    change_pct: float
    action: str        # RAISE | LOWER | MAINTAIN
    reason_en: str
    reason_bn: str
    confidence: str    # HIGH | MEDIUM | LOW

@dataclass
class DemandPrediction:
    product_id: str
    product_name: str
    units_sold_30d: int
    daily_velocity: float
    predicted_next_30d: int
    trend: str          # RISING | STABLE | FALLING
    confidence: str

@dataclass
class InventoryForecast:
    variant_id: str
    product_id: str
    product_name: str
    variant_name: str
    current_stock: int
    daily_velocity: float
    days_remaining: float
    weeks_remaining: float
    status: str         # CRITICAL | WARNING | LOW | OK | NO_SALES

@dataclass
class RestockItem:
    variant_id: str
    product_id: str
    product_name: str
    variant_name: str
    current_stock: int
    recommended_qty: int
    priority: str       # CRITICAL | HIGH
    days_remaining: float

@dataclass
class BundleRecommendation:
    product_a_id: str
    product_a_name: str
    product_b_id: str
    product_b_name: str
    co_purchase_count: int
    suggested_discount_pct: float

@dataclass
class SellerItem:
    product_id: str
    product_name: str
    total_units: int
    total_revenue: float
    order_count: int
    avg_price: float

@dataclass
class CustomerLTV:
    customer_id: str
    customer_name: str
    phone: str
    total_orders: int
    total_spent: float
    avg_order_value: float
    predicted_ltv_12m: float
    segment: str        # PLATINUM | GOLD | SILVER | BRONZE

@dataclass
class ChurnRisk:
    customer_id: str
    customer_name: str
    phone: str
    days_inactive: int
    last_order_date: str
    risk_level: str     # HIGH | MEDIUM | LOW
    total_orders: int

@dataclass
class RevenueForecast:
    current_30d: float
    predicted_next_30d: float
    growth_pct: float
    trend: str
    confidence: str
    daily_points: list[dict] = field(default_factory=list)

@dataclass
class HealthComponent:
    name: str
    name_bn: str
    score: int
    max_score: int
    status: str

@dataclass
class BusinessHealthScore:
    score: int
    grade: str          # A | B | C | D | F
    components: list[HealthComponent]
    strengths: list[str]
    weaknesses: list[str]
    explanation_en: str
    explanation_bn: str

@dataclass
class ProfitReport:
    period_days: int
    total_revenue: float
    estimated_cogs: float
    gross_profit: float
    gross_margin_pct: float
    total_discounts: float
    total_shipping_cost: float
    net_profit: float
    net_margin_pct: float
    delivered_order_count: int
    total_order_count: int

@dataclass
class TaxSummary:
    period_days: int
    total_revenue: float
    vat_rate_pct: float
    estimated_vat: float
    gross_profit: float
    estimated_income_tax: float
    total_tax_liability: float
    deductible_shipping: float
    deductible_discounts: float
    net_tax_after_deductions: float


# ── Engine ─────────────────────────────────────────────────────────────────────

class CommerceEngine:

    # ── Price Recommendations ──────────────────────────────────────────────────

    async def price_recommendations(self, db: AsyncSession, merchant_id: str) -> list[PriceRecommendation]:
        since_30 = datetime.now(UTC) - timedelta(days=30)
        # Products with their sales
        rows = await db.execute(
            select(
                Product.id, Product.name, Product.name_bangla,
                Product.base_price, Product.sale_price,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_30d"),
                func.coalesce(func.sum(OrderItem.total_price), 0).label("rev_30d"),
            )
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id)
                & (Order.created_at >= since_30)
                & (Order.status == OrderStatus.DELIVERED),
            )
            .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
            .group_by(Product.id)
            .order_by(Product.name)
            .limit(50)
        )
        results: list[PriceRecommendation] = []
        for r in rows.all():
            sale = float(r.sale_price or r.base_price)
            base = float(r.base_price)
            units = int(r.units_30d)
            discount_pct = (base - sale) / base * 100 if base > 0 else 0

            if units == 0 and discount_pct < 10:
                action = "LOWER"
                rec_price = round(sale * 0.90, 2)
                change_pct = -10.0
                reason_en = "No sales in 30 days — a 10% discount may stimulate demand."
                reason_bn = "৩০ দিনে কোনো বিক্রি নেই — ১০% ছাড় চাহিদা তৈরি করতে পারে।"
                confidence = "MEDIUM"
            elif units >= 20 and discount_pct > 20:
                action = "RAISE"
                rec_price = round(sale * 1.08, 2)
                change_pct = 8.0
                reason_en = "High demand despite deep discount — consider raising price slightly."
                reason_bn = "বড় ছাড় সত্ত্বেও চাহিদা বেশি — দাম সামান্য বাড়ানো যায়।"
                confidence = "HIGH"
            elif units >= 10 and discount_pct < 5:
                action = "MAINTAIN"
                rec_price = sale
                change_pct = 0.0
                reason_en = "Healthy sales at current price — maintain pricing strategy."
                reason_bn = "বর্তমান দামে ভালো বিক্রি — মূল্য কৌশল বজায় রাখুন।"
                confidence = "HIGH"
            else:
                action = "MAINTAIN"
                rec_price = sale
                change_pct = 0.0
                reason_en = "Insufficient data to make a strong recommendation."
                reason_bn = "সুনির্দিষ্ট সুপারিশ করার জন্য পর্যাপ্ত ডেটা নেই।"
                confidence = "LOW"

            name = r.name_bangla or r.name
            results.append(PriceRecommendation(
                product_id=r.id, product_name=r.name,
                current_price=sale, recommended_price=rec_price,
                change_pct=change_pct, action=action,
                reason_en=reason_en, reason_bn=reason_bn,
                confidence=confidence,
            ))
        return results

    # ── Demand Predictions ────────────────────────────────────────────────────

    async def demand_predictions(self, db: AsyncSession, merchant_id: str) -> list[DemandPrediction]:
        since_30 = datetime.now(UTC) - timedelta(days=30)
        since_60 = datetime.now(UTC) - timedelta(days=60)
        rows = await db.execute(
            select(
                Product.id, Product.name,
                func.coalesce(func.sum(OrderItem.quantity).filter(Order.created_at >= since_30), 0).label("u30"),
                func.coalesce(func.sum(OrderItem.quantity).filter(
                    Order.created_at >= since_60, Order.created_at < since_30), 0).label("u60"),
            )
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .outerjoin(Order, (Order.id == OrderItem.order_id) & (Order.status == OrderStatus.DELIVERED))
            .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
            .group_by(Product.id)
            .order_by(func.coalesce(func.sum(OrderItem.quantity).filter(Order.created_at >= since_30), 0).desc())
            .limit(30)
        )
        out: list[DemandPrediction] = []
        for r in rows.all():
            u30 = int(r.u30)
            u60 = int(r.u60)
            velocity = round(u30 / 30, 2)
            predicted = round(velocity * 30)
            if u30 > u60 * 1.2:
                trend = "RISING"
            elif u30 < u60 * 0.8:
                trend = "FALLING"
            else:
                trend = "STABLE"
            confidence = "HIGH" if u30 >= 10 else ("MEDIUM" if u30 >= 3 else "LOW")
            out.append(DemandPrediction(
                product_id=r.id, product_name=r.name,
                units_sold_30d=u30, daily_velocity=velocity,
                predicted_next_30d=max(predicted, 0),
                trend=trend, confidence=confidence,
            ))
        return out

    # ── Inventory Forecast ────────────────────────────────────────────────────

    async def inventory_forecast(self, db: AsyncSession, merchant_id: str) -> list[InventoryForecast]:
        since_30 = datetime.now(UTC) - timedelta(days=30)
        rows = await db.execute(
            select(
                ProductVariant.id, ProductVariant.name, ProductVariant.stock_quantity,
                Product.id.label("product_id"), Product.name.label("product_name"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_30d"),
            )
            .join(Product, Product.id == ProductVariant.product_id)
            .outerjoin(OrderItem, OrderItem.variant_id == ProductVariant.id)
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id)
                & (Order.created_at >= since_30)
                & (Order.status == OrderStatus.DELIVERED),
            )
            .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
            .group_by(ProductVariant.id, Product.id)
            .order_by(Product.name, ProductVariant.name)
        )
        out: list[InventoryForecast] = []
        for r in rows.all():
            stock = int(r.stock_quantity or 0)
            units_30d = int(r.units_30d)
            velocity = units_30d / 30.0
            if velocity > 0:
                days_rem = stock / velocity
                weeks_rem = days_rem / 7
                if days_rem <= 7:   status = "CRITICAL"
                elif days_rem <= 14: status = "WARNING"
                elif days_rem <= 30: status = "LOW"
                else:                status = "OK"
            else:
                days_rem = 9999.0
                weeks_rem = 9999.0
                status = "NO_SALES"

            out.append(InventoryForecast(
                variant_id=r.id, product_id=r.product_id,
                product_name=r.product_name, variant_name=r.name or r.product_name,
                current_stock=stock, daily_velocity=round(velocity, 2),
                days_remaining=round(days_rem, 1), weeks_remaining=round(weeks_rem, 1),
                status=status,
            ))
        return out

    # ── Restock Recommendations ───────────────────────────────────────────────

    async def restock_recommendations(self, db: AsyncSession, merchant_id: str) -> list[RestockItem]:
        forecasts = await self.inventory_forecast(db, merchant_id)
        out: list[RestockItem] = []
        for f in forecasts:
            if f.status in ("CRITICAL", "WARNING"):
                priority = "CRITICAL" if f.status == "CRITICAL" else "HIGH"
                rec_qty = max(int(f.daily_velocity * 30), 10)
                out.append(RestockItem(
                    variant_id=f.variant_id, product_id=f.product_id,
                    product_name=f.product_name, variant_name=f.variant_name,
                    current_stock=f.current_stock, recommended_qty=rec_qty,
                    priority=priority, days_remaining=f.days_remaining,
                ))
        out.sort(key=lambda x: (0 if x.priority == "CRITICAL" else 1, x.days_remaining))
        return out

    # ── Bundle Recommendations ────────────────────────────────────────────────

    async def bundle_recommendations(self, db: AsyncSession, merchant_id: str) -> list[BundleRecommendation]:
        # Subquery: orders belonging to this merchant
        merchant_orders = (
            select(Order.id)
            .where(Order.merchant_id == merchant_id, Order.status == OrderStatus.DELIVERED)
            .scalar_subquery()
        )
        # Self-join on order_items to find co-purchased products
        oi_a = OrderItem.__table__.alias("oi_a")
        oi_b = OrderItem.__table__.alias("oi_b")
        stmt = (
            select(
                oi_a.c.product_id.label("pid_a"),
                oi_b.c.product_id.label("pid_b"),
                func.count().label("freq"),
            )
            .select_from(oi_a.join(oi_b,
                (oi_a.c.order_id == oi_b.c.order_id) & (oi_a.c.product_id < oi_b.c.product_id)
            ))
            .where(oi_a.c.order_id.in_(merchant_orders))
            .group_by(oi_a.c.product_id, oi_b.c.product_id)
            .order_by(func.count().desc())
            .limit(10)
        )
        rows = await db.execute(stmt)
        pairs = rows.all()
        if not pairs:
            return []

        all_ids = set()
        for r in pairs:
            all_ids.add(r.pid_a)
            all_ids.add(r.pid_b)

        prod_rows = await db.execute(
            select(Product.id, Product.name).where(Product.id.in_(list(all_ids)))
        )
        prod_map = {r.id: r.name for r in prod_rows.all()}

        out: list[BundleRecommendation] = []
        for r in pairs:
            name_a = prod_map.get(r.pid_a, r.pid_a)
            name_b = prod_map.get(r.pid_b, r.pid_b)
            out.append(BundleRecommendation(
                product_a_id=r.pid_a, product_a_name=name_a,
                product_b_id=r.pid_b, product_b_name=name_b,
                co_purchase_count=int(r.freq),
                suggested_discount_pct=5.0 if r.freq >= 5 else 3.0,
            ))
        return out

    # ── Best / Worst Sellers ──────────────────────────────────────────────────

    async def best_sellers(self, db: AsyncSession, merchant_id: str, days: int = 30) -> list[SellerItem]:
        return await self._sellers(db, merchant_id, days, best=True)

    async def worst_sellers(self, db: AsyncSession, merchant_id: str, days: int = 30) -> list[SellerItem]:
        return await self._sellers(db, merchant_id, days, best=False)

    async def _sellers(self, db: AsyncSession, merchant_id: str, days: int, best: bool) -> list[SellerItem]:
        since = datetime.now(UTC) - timedelta(days=days)
        rows = await db.execute(
            select(
                Product.id, Product.name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
                func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"),
                func.count(Order.id.distinct()).label("order_cnt"),
            )
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id)
                & (Order.created_at >= since)
                & (Order.status == OrderStatus.DELIVERED),
            )
            .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
            .group_by(Product.id)
            .order_by(func.coalesce(func.sum(OrderItem.total_price), 0).desc() if best
                      else func.coalesce(func.sum(OrderItem.total_price), 0).asc())
            .limit(10)
        )
        out: list[SellerItem] = []
        for r in rows.all():
            units = int(r.units)
            revenue = float(r.revenue)
            out.append(SellerItem(
                product_id=r.id, product_name=r.name,
                total_units=units, total_revenue=revenue,
                order_count=int(r.order_cnt),
                avg_price=round(revenue / units, 2) if units > 0 else 0.0,
            ))
        return out

    # ── Customer LTV ──────────────────────────────────────────────────────────

    async def customer_ltv(self, db: AsyncSession, merchant_id: str) -> list[CustomerLTV]:
        rows = await db.execute(
            select(Customer)
            .where(Customer.merchant_id == merchant_id, Customer.total_orders > 0)
            .order_by(Customer.total_spent.desc())
            .limit(50)
        )
        out: list[CustomerLTV] = []
        customers = rows.scalars().all()
        if not customers:
            return []
        max_spent = float(customers[0].total_spent) if customers else 1.0

        for c in customers:
            spent = float(c.total_spent)
            orders = int(c.total_orders)
            avg_order = spent / orders if orders > 0 else 0.0
            # LTV = avg_order * (orders / months_active) * 12
            months_since = max(1, (datetime.now(UTC) - c.created_at).days // 30) if hasattr(c, "created_at") and c.created_at else 12
            purchase_freq_monthly = orders / max(months_since, 1)
            ltv_12m = round(avg_order * purchase_freq_monthly * 12, 2)

            ratio = spent / max_spent if max_spent > 0 else 0
            if ratio >= 0.6:   segment = "PLATINUM"
            elif ratio >= 0.3: segment = "GOLD"
            elif ratio >= 0.1: segment = "SILVER"
            else:               segment = "BRONZE"

            out.append(CustomerLTV(
                customer_id=c.id, customer_name=c.name, phone=c.phone,
                total_orders=orders, total_spent=spent,
                avg_order_value=round(avg_order, 2),
                predicted_ltv_12m=ltv_12m, segment=segment,
            ))
        return out

    # ── Churn Prediction ──────────────────────────────────────────────────────

    async def churn_risk(self, db: AsyncSession, merchant_id: str) -> list[ChurnRisk]:
        since_30 = datetime.now(UTC) - timedelta(days=30)
        rows = await db.execute(
            select(Customer)
            .where(
                Customer.merchant_id == merchant_id,
                Customer.last_order_at.is_not(None),
                Customer.last_order_at < since_30,
            )
            .order_by(Customer.last_order_at.asc())
            .limit(100)
        )
        now = datetime.now(UTC)
        out: list[ChurnRisk] = []
        for c in rows.scalars().all():
            lo = c.last_order_at
            if lo.tzinfo is None:
                lo = lo.replace(tzinfo=UTC)
            days_inactive = (now - lo).days
            if days_inactive >= 90:   risk = "HIGH"
            elif days_inactive >= 60: risk = "MEDIUM"
            else:                     risk = "LOW"
            out.append(ChurnRisk(
                customer_id=c.id, customer_name=c.name, phone=c.phone,
                days_inactive=days_inactive,
                last_order_date=lo.strftime("%Y-%m-%d"),
                risk_level=risk, total_orders=int(c.total_orders),
            ))
        out.sort(key=lambda x: x.days_inactive, reverse=True)
        return out

    # ── Revenue Forecast ──────────────────────────────────────────────────────

    async def revenue_forecast(self, db: AsyncSession, merchant_id: str) -> RevenueForecast:
        since_60 = datetime.now(UTC) - timedelta(days=60)
        since_30 = datetime.now(UTC) - timedelta(days=30)

        day_col = cast(Order.created_at, Date)
        rows = await db.execute(
            select(
                day_col.label("day"),
                func.coalesce(func.sum(Order.total_amount), 0).label("rev"),
            )
            .where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since_60,
                Order.status == OrderStatus.DELIVERED,
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        daily = {str(r.day): float(r.rev) for r in rows.all()}

        rev_30 = sum(v for k, v in daily.items() if k >= since_30.date().isoformat())
        rev_prev = sum(v for k, v in daily.items() if k < since_30.date().isoformat())

        if rev_prev > 0:
            growth_pct = round((rev_30 - rev_prev) / rev_prev * 100, 1)
        elif rev_30 > 0:
            growth_pct = 100.0
        else:
            growth_pct = 0.0

        # Simple linear extrapolation
        vals = list(daily.values())
        if len(vals) >= 3:
            n = len(vals)
            mx = sum(range(n)) / n
            my = sum(vals) / n
            num = sum((i - mx) * (v - my) for i, v in enumerate(vals))
            den = sum((i - mx) ** 2 for i in range(n)) or 1
            slope = num / den
            predicted = max(0.0, round(sum(vals[-7:]) / max(len(vals[-7:]), 1) * 30 + slope * 15, 2))
        else:
            predicted = round(rev_30, 2)

        if growth_pct > 5:   trend = "RISING"
        elif growth_pct < -5: trend = "FALLING"
        else:                  trend = "STABLE"

        confidence = "HIGH" if len(daily) >= 14 else ("MEDIUM" if len(daily) >= 7 else "LOW")
        points = [{"date": k, "revenue": v} for k, v in sorted(daily.items())]

        return RevenueForecast(
            current_30d=round(rev_30, 2), predicted_next_30d=predicted,
            growth_pct=growth_pct, trend=trend, confidence=confidence,
            daily_points=points,
        )

    # ── Business Health Score ─────────────────────────────────────────────────

    async def health_score(self, db: AsyncSession, merchant_id: str) -> BusinessHealthScore:
        since_30 = datetime.now(UTC) - timedelta(days=30)
        since_7  = datetime.now(UTC) - timedelta(days=7)

        # Revenue trend
        forecast = await self.revenue_forecast(db, merchant_id)
        revenue_score = 25 if forecast.trend == "RISING" else (15 if forecast.trend == "STABLE" else 5)

        # Order fulfillment rate
        total_r = await db.execute(
            select(func.count(Order.id)).where(Order.merchant_id == merchant_id, Order.created_at >= since_30)
        )
        delivered_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id, Order.created_at >= since_30,
                Order.status == OrderStatus.DELIVERED,
            )
        )
        total_orders = int(total_r.scalar_one() or 0)
        delivered = int(delivered_r.scalar_one() or 0)
        fulfill_rate = delivered / total_orders if total_orders > 0 else 0
        fulfill_score = round(fulfill_rate * 25)

        # Inventory health
        forecasts = await self.inventory_forecast(db, merchant_id)
        if forecasts:
            ok_count = sum(1 for f in forecasts if f.status in ("OK", "NO_SALES"))
            inv_score = round(ok_count / len(forecasts) * 20)
        else:
            inv_score = 10

        # Customer retention
        cust_r = await db.execute(select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id))
        repeat_r = await db.execute(
            select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id, Customer.total_orders > 1)
        )
        total_cust = int(cust_r.scalar_one() or 0)
        repeat_cust = int(repeat_r.scalar_one() or 0)
        retention = repeat_cust / total_cust if total_cust > 0 else 0
        retention_score = round(retention * 15)

        # Payment collection
        paid_r = await db.execute(
            select(func.coalesce(func.sum(Order.paid_amount), 0)).where(
                Order.merchant_id == merchant_id, Order.created_at >= since_30
            )
        )
        total_rev_r = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id, Order.created_at >= since_30
            )
        )
        paid = float(paid_r.scalar_one() or 0)
        total_rev = float(total_rev_r.scalar_one() or 0)
        collection_rate = paid / total_rev if total_rev > 0 else 0
        collection_score = round(collection_rate * 15)

        score = revenue_score + fulfill_score + inv_score + retention_score + collection_score
        score = max(0, min(100, score))

        if score >= 80:   grade = "A"
        elif score >= 65: grade = "B"
        elif score >= 50: grade = "C"
        elif score >= 35: grade = "D"
        else:             grade = "F"

        components = [
            HealthComponent("Revenue Trend", "রাজস্ব প্রবণতা", revenue_score, 25,
                            "GOOD" if revenue_score >= 20 else ("OK" if revenue_score >= 12 else "POOR")),
            HealthComponent("Order Fulfillment", "অর্ডার পূরণ", fulfill_score, 25,
                            "GOOD" if fulfill_score >= 20 else ("OK" if fulfill_score >= 12 else "POOR")),
            HealthComponent("Inventory Health", "ইনভেন্টরি স্বাস্থ্য", inv_score, 20,
                            "GOOD" if inv_score >= 16 else ("OK" if inv_score >= 10 else "POOR")),
            HealthComponent("Customer Retention", "গ্রাহক ধারণ", retention_score, 15,
                            "GOOD" if retention_score >= 10 else ("OK" if retention_score >= 6 else "POOR")),
            HealthComponent("Payment Collection", "পেমেন্ট সংগ্রহ", collection_score, 15,
                            "GOOD" if collection_score >= 12 else ("OK" if collection_score >= 7 else "POOR")),
        ]

        strengths = [c.name for c in components if c.status == "GOOD"]
        weaknesses = [c.name for c in components if c.status == "POOR"]

        explanation_en = (
            f"Your business health score is {score}/100 (Grade {grade}). "
            f"Strengths: {', '.join(strengths) or 'None identified'}. "
            f"Areas for improvement: {', '.join(weaknesses) or 'None — keep it up!'}."
        )
        explanation_bn = (
            f"আপনার ব্যবসার স্বাস্থ্য স্কোর {score}/100 (গ্রেড {grade})। "
            f"শক্তিশালী দিক: {', '.join(strengths) or 'কোনোটি নয়'}। "
            f"উন্নতির ক্ষেত্র: {', '.join(weaknesses) or 'কোনোটি নয় — চালিয়ে যান!'}।"
        )

        return BusinessHealthScore(
            score=score, grade=grade, components=components,
            strengths=strengths, weaknesses=weaknesses,
            explanation_en=explanation_en, explanation_bn=explanation_bn,
        )

    # ── Profit Report ─────────────────────────────────────────────────────────

    async def profit_report(self, db: AsyncSession, merchant_id: str, days: int = 30) -> ProfitReport:
        since = datetime.now(UTC) - timedelta(days=days)

        rev_r = await db.execute(
            select(
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
                func.coalesce(func.sum(Order.discount_amount), 0).label("discounts"),
                func.coalesce(func.sum(Order.shipping_cost), 0).label("shipping"),
                func.count(Order.id).label("delivered"),
            )
            .where(
                Order.merchant_id == merchant_id,
                Order.created_at >= since,
                Order.status == OrderStatus.DELIVERED,
            )
        )
        total_r = await db.execute(
            select(func.count(Order.id)).where(Order.merchant_id == merchant_id, Order.created_at >= since)
        )
        row = rev_r.one()
        revenue = float(row.revenue)
        discounts = float(row.discounts)
        shipping = float(row.shipping)
        delivered = int(row.delivered)
        total_orders = int(total_r.scalar_one() or 0)

        # Estimated COGS: 60% of revenue (industry average for e-commerce, no product cost data)
        cogs = round(revenue * 0.60, 2)
        gross_profit = round(revenue - cogs, 2)
        gross_margin = round(gross_profit / revenue * 100, 1) if revenue > 0 else 0
        net_profit = round(gross_profit - discounts - shipping, 2)
        net_margin = round(net_profit / revenue * 100, 1) if revenue > 0 else 0

        return ProfitReport(
            period_days=days, total_revenue=round(revenue, 2),
            estimated_cogs=cogs, gross_profit=gross_profit,
            gross_margin_pct=gross_margin, total_discounts=round(discounts, 2),
            total_shipping_cost=round(shipping, 2), net_profit=net_profit,
            net_margin_pct=net_margin, delivered_order_count=delivered,
            total_order_count=total_orders,
        )

    # ── Tax Summary ───────────────────────────────────────────────────────────

    async def tax_summary(self, db: AsyncSession, merchant_id: str, days: int = 30) -> TaxSummary:
        profit = await self.profit_report(db, merchant_id, days)
        vat_rate = 15.0  # Bangladesh VAT
        estimated_vat = round(profit.total_revenue * vat_rate / 100, 2)
        income_tax = round(max(0, profit.net_profit) * 0.25, 2)  # Simplified 25% on net profit
        total_tax = round(estimated_vat + income_tax, 2)
        deductible_exp = round(profit.total_discounts + profit.total_shipping_cost, 2)
        net_tax = round(max(0, total_tax - deductible_exp * 0.15), 2)

        return TaxSummary(
            period_days=days, total_revenue=profit.total_revenue,
            vat_rate_pct=vat_rate, estimated_vat=estimated_vat,
            gross_profit=profit.gross_profit,
            estimated_income_tax=income_tax, total_tax_liability=total_tax,
            deductible_shipping=profit.total_shipping_cost,
            deductible_discounts=profit.total_discounts,
            net_tax_after_deductions=net_tax,
        )

    # ── Notifications ─────────────────────────────────────────────────────────

    async def get_notifications(self, db: AsyncSession, merchant_id: str) -> list[dict]:
        notifications: list[dict] = []

        # ── Pending orders needing action ─────────────────────────────────────
        pending_q = select(func.count()).where(
            Order.merchant_id == merchant_id,
            Order.status == OrderStatus.PENDING,
        )
        pending_count: int = (await db.execute(pending_q)).scalar() or 0
        if pending_count >= 3:
            notifications.append({
                "id": "pending_orders",
                "type": "PENDING_ORDERS",
                "priority": "HIGH",
                "title_en": f"{pending_count} Orders Awaiting Processing",
                "title_bn": f"{pending_count}টি অর্ডার প্রক্রিয়াকরণের অপেক্ষায়",
                "body_en": "Review and confirm pending orders to avoid delivery delays.",
                "body_bn": "ডেলিভারি বিলম্ব এড়াতে পেন্ডিং অর্ডারগুলো রিভিউ করুন।",
                "action": "/orders",
            })
        elif pending_count > 0:
            notifications.append({
                "id": "pending_orders",
                "type": "PENDING_ORDERS",
                "priority": "MEDIUM",
                "title_en": f"{pending_count} Pending Order{'s' if pending_count > 1 else ''}",
                "title_bn": f"{pending_count}টি পেন্ডিং অর্ডার",
                "body_en": "Confirm and assign courier to pending orders.",
                "body_bn": "পেন্ডিং অর্ডারে কুরিয়ার নির্ধারণ করুন।",
                "action": "/orders",
            })

        # ── COD collection due ─────────────────────────────────────────────────
        cod_due_q = select(
            func.count().label("cnt"),
            func.sum(Order.due_amount).label("total_due"),
        ).where(
            Order.merchant_id == merchant_id,
            Order.payment_method == PaymentMethod.COD,
            Order.payment_status == PaymentStatus.UNPAID,
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED]),
        )
        cod_row = (await db.execute(cod_due_q)).one_or_none()
        cod_count = cod_row.cnt if cod_row else 0
        cod_due = float(cod_row.total_due or 0) if cod_row else 0.0
        if cod_count and cod_count > 0:
            notifications.append({
                "id": "cod_collection",
                "type": "COD_COLLECTION",
                "priority": "MEDIUM",
                "title_en": f"৳{cod_due:,.0f} COD Collection Pending",
                "title_bn": f"৳{cod_due:,.0f} কালেকশন বাকি",
                "body_en": f"{cod_count} COD orders in transit — follow up with riders for collection.",
                "body_bn": f"{cod_count}টি কোড অর্ডার ডেলিভারিতে — রাইডার থেকে কালেকশন নিন।",
                "action": "/orders",
            })

        # ── Unpaid dues across all methods ────────────────────────────────────
        unpaid_q = select(
            func.count().label("cnt"),
            func.sum(Order.due_amount).label("total"),
        ).where(
            Order.merchant_id == merchant_id,
            Order.payment_status == PaymentStatus.UNPAID,
            Order.due_amount > 0,
            Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.PENDING]),
        )
        unpaid_row = (await db.execute(unpaid_q)).one_or_none()
        unpaid_count = unpaid_row.cnt if unpaid_row else 0
        unpaid_total = float(unpaid_row.total or 0) if unpaid_row else 0.0
        if unpaid_count and unpaid_count > 0 and cod_count == 0:
            notifications.append({
                "id": "unpaid_dues",
                "type": "PAYMENT_DUE",
                "priority": "MEDIUM",
                "title_en": f"৳{unpaid_total:,.0f} Payment Due",
                "title_bn": f"৳{unpaid_total:,.0f} পেমেন্ট বাকি",
                "body_en": f"{unpaid_count} confirmed orders have outstanding payments.",
                "body_bn": f"{unpaid_count}টি কনফার্মড অর্ডারের পেমেন্ট এখনও বাকি।",
                "action": "/orders",
            })

        # ── Low stock alerts (ProductVariant-based if available) ──────────────
        forecasts = await self.inventory_forecast(db, merchant_id)
        for f in forecasts[:5]:
            if f.status == "CRITICAL":
                notifications.append({
                    "id": f"stock_{f.variant_id}",
                    "type": "LOW_STOCK",
                    "priority": "HIGH",
                    "title_en": f"Critical Stock: {f.product_name}",
                    "title_bn": f"স্টক শেষ হচ্ছে: {f.product_name}",
                    "body_en": f"Only {f.current_stock} units left — runs out in {f.days_remaining:.0f} days.",
                    "body_bn": f"মাত্র {f.current_stock}টি বাকি — {f.days_remaining:.0f} দিনে শেষ হবে।",
                    "action": "/inventory",
                })
            elif f.status == "WARNING":
                notifications.append({
                    "id": f"stock_{f.variant_id}",
                    "type": "LOW_STOCK",
                    "priority": "MEDIUM",
                    "title_en": f"Low Stock: {f.product_name}",
                    "title_bn": f"কম স্টক: {f.product_name}",
                    "body_en": f"{f.current_stock} units remaining — {f.days_remaining:.0f} days of stock.",
                    "body_bn": f"{f.current_stock}টি বাকি — {f.days_remaining:.0f} দিনের স্টক।",
                    "action": "/inventory",
                })

        # ── Churn alerts ──────────────────────────────────────────────────────
        churn = await self.churn_risk(db, merchant_id)
        high_risk = [c for c in churn if c.risk_level == "HIGH"]
        if high_risk:
            others = len(high_risk) - 1
            body_en = (
                f"{high_risk[0].customer_name} and {others} others haven't ordered in 90+ days."
                if others > 0
                else f"{high_risk[0].customer_name} hasn't ordered in 90+ days."
            )
            body_bn = (
                f"{high_risk[0].customer_name} সহ {others} জন ৯০+ দিন ধরে নিষ্ক্রিয়।"
                if others > 0
                else f"{high_risk[0].customer_name} ৯০+ দিন ধরে নিষ্ক্রিয়।"
            )
            notifications.append({
                "id": "churn_high",
                "type": "CHURN_RISK",
                "priority": "HIGH",
                "title_en": f"{len(high_risk)} Customer{'s' if len(high_risk) > 1 else ''} at Risk of Churning",
                "title_bn": f"{len(high_risk)} জন গ্রাহক হারানোর ঝুঁকিতে",
                "body_en": body_en,
                "body_bn": body_bn,
                "action": "/reports",
            })
        medium_risk = [c for c in churn if c.risk_level == "MEDIUM"]
        if medium_risk and not high_risk:
            notifications.append({
                "id": "churn_medium",
                "type": "CHURN_RISK",
                "priority": "MEDIUM",
                "title_en": f"{len(medium_risk)} Customers Need Re-engagement",
                "title_bn": f"{len(medium_risk)} জন গ্রাহককে পুনরায় সক্রিয় করুন",
                "body_en": "These customers haven't bought in 30–60 days. Send a promo.",
                "body_bn": "এই গ্রাহকরা ৩০–৬০ দিন ধরে কেনেননি। প্রমোশন পাঠান।",
                "action": "/reports",
            })

        # ── Top seller milestone ──────────────────────────────────────────────
        top_q = select(Product.name, Product.total_sold).where(
            Product.merchant_id == merchant_id,
            Product.is_published.is_(True),
            Product.total_sold > 10,
        ).order_by(Product.total_sold.desc()).limit(1)
        top_row = (await db.execute(top_q)).one_or_none()
        if top_row:
            notifications.append({
                "id": "top_seller",
                "type": "BEST_SELLER",
                "priority": "LOW",
                "title_en": f"Best Seller: {top_row.name}",
                "title_bn": f"সেরা পণ্য: {top_row.name}",
                "body_en": f"{top_row.total_sold} units sold — keep it well stocked.",
                "body_bn": f"{top_row.total_sold}টি বিক্রি হয়েছে — স্টক ঠিক রাখুন।",
                "action": "/products",
            })

        # ── Revenue trend ─────────────────────────────────────────────────────
        forecast = await self.revenue_forecast(db, merchant_id)
        if forecast.trend == "FALLING" and forecast.current_30d > 0:
            notifications.append({
                "id": "revenue_drop",
                "type": "REVENUE_ALERT",
                "priority": "HIGH",
                "title_en": f"Revenue Declining ({forecast.growth_pct:+.1f}%)",
                "title_bn": f"রাজস্ব কমছে ({forecast.growth_pct:+.1f}%)",
                "body_en": "Revenue is trending down. Consider running promotions or campaigns.",
                "body_bn": "রাজস্ব কমছে। প্রমোশন বা ক্যাম্পেইন চালানোর কথা বিবেচনা করুন।",
                "action": "/commerce",
            })
        elif forecast.trend == "RISING":
            notifications.append({
                "id": "revenue_up",
                "type": "REVENUE_POSITIVE",
                "priority": "LOW",
                "title_en": f"Revenue Growing ({forecast.growth_pct:+.1f}%)",
                "title_bn": f"রাজস্ব বাড়ছে ({forecast.growth_pct:+.1f}%)",
                "body_en": "Great momentum! Ensure stock levels are ready to meet demand.",
                "body_bn": "চমৎকার গতি! চাহিদা পূরণে স্টক প্রস্তুত রাখুন।",
                "action": "/commerce",
            })

        return notifications
