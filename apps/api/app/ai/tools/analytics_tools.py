from datetime import date, timedelta

from langchain_core.tools import tool
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentStatus


def make_analytics_tools(db: AsyncSession, merchant_id: str):
    @tool
    async def get_business_summary(period: str = "today") -> str:
        """
        Get business summary for a time period.
        period: 'today', 'week', 'month'
        """
        today = date.today()

        if period == "today":
            start = today
            label = "আজকের"
        elif period == "week":
            start = today - timedelta(days=7)
            label = "গত ৭ দিনের"
        elif period == "month":
            start = today - timedelta(days=30)
            label = "গত ৩০ দিনের"
        else:
            return "অজানা পিরিয়ড। 'today', 'week', বা 'month' ব্যবহার করুন।"

        revenue_result = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0))
            .where(
                Order.merchant_id == merchant_id,
                Order.status != OrderStatus.CANCELLED,
                Order.created_at >= start,
            )
        )
        revenue = float(revenue_result.scalar() or 0)

        order_count_result = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= start,
            )
        )
        order_count = order_count_result.scalar() or 0

        pending_result = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.status == OrderStatus.PENDING,
                Order.created_at >= start,
            )
        )
        pending = pending_result.scalar() or 0

        unpaid_result = await db.execute(
            select(func.coalesce(func.sum(Order.due_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.payment_status != PaymentStatus.PAID,
                Order.status != OrderStatus.CANCELLED,
                Order.created_at >= start,
            )
        )
        unpaid = float(unpaid_result.scalar() or 0)

        return (
            f"{label} ব্যবসার সারাংশ:\n"
            f"• মোট বিক্রয়: ৳{revenue:,.0f}\n"
            f"• মোট অর্ডার: {order_count}টি\n"
            f"• পেন্ডিং অর্ডার: {pending}টি\n"
            f"• বকেয়া পাওনা: ৳{unpaid:,.0f}"
        )

    return [get_business_summary]
