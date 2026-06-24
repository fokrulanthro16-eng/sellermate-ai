from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order, OrderStatus
from app.models.product import ProductVariant
from app.schemas.merchant import DashboardStats, OnboardingStepRequest, UpdateMerchantRequest


async def get_by_id(db: AsyncSession, merchant_id: str) -> Merchant:
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise NotFoundException("Merchant not found")
    return merchant


async def update(
    db: AsyncSession, merchant_id: str, data: UpdateMerchantRequest
) -> Merchant:
    merchant = await get_by_id(db, merchant_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(merchant, field, value)
    return merchant


async def complete_onboarding_step(
    db: AsyncSession, merchant_id: str, req: OnboardingStepRequest
) -> Merchant:
    merchant = await get_by_id(db, merchant_id)

    step_handlers = {
        1: _handle_business_info,
        2: _handle_categories,
        3: _handle_whatsapp,
        4: _handle_first_product,
    }

    handler = step_handlers.get(req.step)
    if handler:
        handler(merchant, req.data)

    merchant.onboarding_step = max(merchant.onboarding_step, req.step)
    if merchant.onboarding_step >= 4:
        merchant.onboarding_done = True

    return merchant


async def get_dashboard_stats(db: AsyncSession, merchant_id: str) -> DashboardStats:
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    async def _revenue(from_dt: datetime, to_dt: datetime) -> float:
        result = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= from_dt,
                Order.created_at < to_dt,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        return float(result.scalar_one())

    async def _order_count(from_dt: datetime, to_dt: datetime) -> int:
        result = await db.execute(
            select(func.count()).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= from_dt,
                Order.created_at < to_dt,
            )
        )
        return result.scalar_one()

    today_revenue, yesterday_revenue = (
        await _revenue(today, today + timedelta(days=1)),
        await _revenue(yesterday, today),
    )
    today_orders, yesterday_orders = (
        await _order_count(today, today + timedelta(days=1)),
        await _order_count(yesterday, today),
    )

    pending_result = await db.execute(
        select(func.count()).where(
            Order.merchant_id == merchant_id,
            Order.status == OrderStatus.PENDING,
        )
    )
    pending_orders = pending_result.scalar_one()

    low_stock_result = await db.execute(
        select(func.count()).where(
            ProductVariant.product.has(merchant_id=merchant_id),
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
    )
    low_stock_variants = low_stock_result.scalar_one()

    new_customers_result = await db.execute(
        select(func.count()).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= today,
        )
    )
    new_customers_today = new_customers_result.scalar_one()

    def _pct_change(current: float, previous: float) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    return DashboardStats(
        today_revenue=today_revenue,
        today_orders=today_orders,
        pending_orders=pending_orders,
        low_stock_variants=low_stock_variants,
        new_customers_today=new_customers_today,
        revenue_change_pct=_pct_change(today_revenue, yesterday_revenue),
        orders_change_pct=_pct_change(float(today_orders), float(yesterday_orders)),
    )


# ── Onboarding step handlers ──────────────────────────────────────────────────


def _handle_business_info(merchant: Merchant, data: dict) -> None:
    for field in ("address", "district", "division"):
        if field in data:
            setattr(merchant, field, data[field])


def _handle_categories(merchant: Merchant, data: dict) -> None:
    pass  # category preferences stored at product level


def _handle_whatsapp(merchant: Merchant, data: dict) -> None:
    if "phone" in data:
        merchant.whatsapp_phone = data["phone"]


def _handle_first_product(merchant: Merchant, data: dict) -> None:
    pass  # product creation handled by product_service
