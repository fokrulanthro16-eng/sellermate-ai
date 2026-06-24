from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductVariant
from app.schemas.analytics import (
    ChannelBreakdown,
    CustomerMetricsOut,
    DashboardMetrics,
    InventoryHealthOut,
    OrderBreakdownOut,
    OverviewMetrics,
    RevenuePoint,
    RevenueSeriesOut,
    TopCustomerItem,
    TopProductItem,
)


async def get_overview(
    db: AsyncSession, merchant_id: str, from_date: datetime, to_date: datetime
) -> OverviewMetrics:
    base_where = [
        Order.merchant_id == merchant_id,
        Order.status != OrderStatus.CANCELLED,
        Order.created_at >= from_date,
        Order.created_at <= to_date,
    ]

    # Current period
    result = await db.execute(
        select(
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("orders"),
        ).where(*base_where)
    )
    row = result.one()
    current_revenue = float(row.revenue)
    current_orders = int(row.orders)

    # Prior period (same duration)
    duration = to_date - from_date
    prior_from = from_date - duration
    prior_where = [
        Order.merchant_id == merchant_id,
        Order.status != OrderStatus.CANCELLED,
        Order.created_at >= prior_from,
        Order.created_at < from_date,
    ]
    prior_result = await db.execute(
        select(
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("orders"),
        ).where(*prior_where)
    )
    prior_row = prior_result.one()
    prior_revenue = float(prior_row.revenue)
    prior_orders = int(prior_row.orders)

    # Customers
    current_customers = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= from_date,
            Customer.created_at <= to_date,
        )
    )
    prior_customers = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= prior_from,
            Customer.created_at < from_date,
        )
    )

    def pct(current: float, prior: float) -> float:
        if prior == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - prior) / prior * 100, 1)

    cc = current_customers.scalar_one()
    pc = prior_customers.scalar_one()

    return OverviewMetrics(
        total_revenue=current_revenue,
        total_orders=current_orders,
        total_customers=cc,
        average_order_value=round(current_revenue / current_orders, 2) if current_orders > 0 else 0.0,
        revenue_change_pct=pct(current_revenue, prior_revenue),
        orders_change_pct=pct(float(current_orders), float(prior_orders)),
        customers_change_pct=pct(float(cc), float(pc)),
    )


async def get_revenue_series(
    db: AsyncSession,
    merchant_id: str,
    period: str,
    from_date: datetime,
    to_date: datetime,
) -> RevenueSeriesOut:
    result = await db.execute(
        select(
            func.date_trunc(period, Order.created_at).label("bucket"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .where(
            Order.merchant_id == merchant_id,
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= from_date,
            Order.created_at <= to_date,
        )
        .group_by("bucket")
        .order_by("bucket")
    )
    rows = result.all()

    points = [
        RevenuePoint(
            date=row.bucket.strftime("%Y-%m-%d"),
            revenue=float(row.revenue),
            orders=int(row.orders),
        )
        for row in rows
    ]
    return RevenueSeriesOut(period=period, points=points)


async def get_order_breakdown(
    db: AsyncSession, merchant_id: str, from_date: datetime, to_date: datetime
) -> OrderBreakdownOut:
    base_where = [
        Order.merchant_id == merchant_id,
        Order.created_at >= from_date,
        Order.created_at <= to_date,
    ]

    status_result = await db.execute(
        select(Order.status, func.count(Order.id))
        .where(*base_where)
        .group_by(Order.status)
    )
    channel_result = await db.execute(
        select(
            Order.channel,
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        )
        .where(*base_where)
        .group_by(Order.channel)
    )
    payment_method_result = await db.execute(
        select(Order.payment_method, func.count(Order.id))
        .where(*base_where)
        .group_by(Order.payment_method)
    )
    payment_status_result = await db.execute(
        select(Order.payment_status, func.count(Order.id))
        .where(*base_where)
        .group_by(Order.payment_status)
    )

    return OrderBreakdownOut(
        by_status={str(r[0].value): r[1] for r in status_result.all()},
        by_channel=[
            ChannelBreakdown(channel=r.channel.value, count=r.count, revenue=float(r.revenue))
            for r in channel_result.all()
        ],
        by_payment_method={str(r[0].value): r[1] for r in payment_method_result.all()},
        by_payment_status={str(r[0].value): r[1] for r in payment_status_result.all()},
    )


async def get_top_products(
    db: AsyncSession,
    merchant_id: str,
    from_date: datetime,
    to_date: datetime,
    limit: int = 10,
) -> list[TopProductItem]:
    result = await db.execute(
        select(
            OrderItem.product_id,
            OrderItem.product_name,
            func.sum(OrderItem.total_price).label("total_revenue"),
            func.sum(OrderItem.quantity).label("total_quantity"),
        )
        .join(Order)
        .where(
            Order.merchant_id == merchant_id,
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= from_date,
            Order.created_at <= to_date,
        )
        .group_by(OrderItem.product_id, OrderItem.product_name)
        .order_by(func.sum(OrderItem.total_price).desc())
        .limit(limit)
    )

    return [
        TopProductItem(
            product_id=r.product_id,
            product_name=r.product_name,
            total_revenue=float(r.total_revenue),
            total_quantity=int(r.total_quantity),
        )
        for r in result.all()
    ]


async def get_inventory_health(db: AsyncSession, merchant_id: str) -> InventoryHealthOut:
    result = await db.execute(
        select(
            func.count(ProductVariant.id).label("total"),
            func.sum(case((ProductVariant.stock_quantity > ProductVariant.low_stock_alert, 1), else_=0)).label("in_stock"),
            func.sum(case(((ProductVariant.stock_quantity > 0) & (ProductVariant.stock_quantity <= ProductVariant.low_stock_alert), 1), else_=0)).label("low_stock"),
            func.sum(case((ProductVariant.stock_quantity == 0, 1), else_=0)).label("out_of_stock"),
        )
        .join(Product)
        .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
    )
    row = result.one()

    low_stock_items_result = await db.execute(
        select(ProductVariant.id, ProductVariant.name, ProductVariant.stock_quantity, Product.name.label("product_name"))
        .join(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .order_by(ProductVariant.stock_quantity.asc())
        .limit(20)
    )

    return InventoryHealthOut(
        total_variants=int(row.total or 0),
        in_stock=int(row.in_stock or 0),
        low_stock=int(row.low_stock or 0),
        out_of_stock=int(row.out_of_stock or 0),
        low_stock_items=[
            {"variant_id": r.id, "variant_name": r.name, "product_name": r.product_name, "stock": r.stock_quantity}
            for r in low_stock_items_result.all()
        ],
    )


async def get_dashboard(db: AsyncSession, merchant_id: str) -> DashboardMetrics:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    async def _revenue(from_dt: datetime, to_dt: datetime) -> float:
        r = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.status != OrderStatus.CANCELLED,
                Order.created_at >= from_dt,
                Order.created_at <= to_dt,
            )
        )
        return float(r.scalar_one())

    async def _order_count(from_dt: datetime | None = None, status: OrderStatus | None = None) -> int:
        conditions = [Order.merchant_id == merchant_id]
        if status is not None:
            conditions.append(Order.status == status)
        if from_dt is not None:
            conditions.append(Order.created_at >= from_dt)
        r = await db.execute(select(func.count(Order.id)).where(*conditions))
        return int(r.scalar_one())

    today_revenue = await _revenue(today_start, now)
    weekly_revenue = await _revenue(week_start, now)
    monthly_revenue = await _revenue(month_start, now)

    total_orders = await _order_count(status=None)
    delivered_orders = await _order_count(status=OrderStatus.DELIVERED)
    cancelled_orders = await _order_count(status=OrderStatus.CANCELLED)

    # Monthly order count for AOV
    monthly_orders_r = await db.execute(
        select(func.count(Order.id)).where(
            Order.merchant_id == merchant_id,
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= month_start,
        )
    )
    monthly_order_count = int(monthly_orders_r.scalar_one())
    aov = round(monthly_revenue / monthly_order_count, 2) if monthly_order_count > 0 else 0.0

    repeat_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.total_orders > 1,
        )
    )
    repeat_customers = int(repeat_r.scalar_one())

    top_products = await get_top_products(db, merchant_id, month_start, now, limit=5)

    top_cust_r = await db.execute(
        select(Customer.id, Customer.name, Customer.total_orders, Customer.total_spent)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.total_spent.desc())
        .limit(5)
    )
    top_customers = [
        TopCustomerItem(
            customer_id=str(r.id),
            customer_name=r.name,
            total_orders=r.total_orders,
            total_spent=float(r.total_spent),
        )
        for r in top_cust_r.all()
    ]

    return DashboardMetrics(
        today_revenue=today_revenue,
        weekly_revenue=weekly_revenue,
        monthly_revenue=monthly_revenue,
        total_orders=total_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        repeat_customers=repeat_customers,
        average_order_value=aov,
        top_products=top_products,
        top_customers=top_customers,
    )


async def get_customer_metrics(
    db: AsyncSession, merchant_id: str, from_date: datetime, to_date: datetime
) -> CustomerMetricsOut:
    new_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.created_at >= from_date,
            Customer.created_at <= to_date,
        )
    )
    new_customers = int(new_r.scalar_one())

    returning_r = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.merchant_id == merchant_id,
            Customer.total_orders > 1,
        )
    )
    returning_customers = int(returning_r.scalar_one())

    top_r = await db.execute(
        select(Customer.id, Customer.name, Customer.total_orders, Customer.total_spent)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.total_spent.desc())
        .limit(10)
    )
    top_customers = [
        {
            "customer_id": str(r.id),
            "customer_name": r.name,
            "total_orders": r.total_orders,
            "total_spent": float(r.total_spent),
        }
        for r in top_r.all()
    ]

    return CustomerMetricsOut(
        new_customers=new_customers,
        returning_customers=returning_customers,
        top_customers=top_customers,
    )
