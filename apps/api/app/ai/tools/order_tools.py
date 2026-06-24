from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus


def make_order_tools(db: AsyncSession, merchant_id: str):
    @tool
    async def search_orders(query: str, status: str = "") -> str:
        """
        Search orders by order number or customer name/phone.
        Optionally filter by status: pending, confirmed, processing, shipped, delivered, cancelled.
        """
        from app.models.customer import Customer

        stmt = (
            select(Order)
            .join(Customer, Order.customer_id == Customer.id, isouter=True)
            .options(selectinload(Order.customer))
            .where(Order.merchant_id == merchant_id)
        )

        if status:
            try:
                status_enum = OrderStatus(status.upper())
                stmt = stmt.where(Order.status == status_enum)
            except ValueError:
                return f"অজানা স্ট্যাটাস: {status}"

        if query:
            stmt = stmt.where(
                Order.order_number.ilike(f"%{query}%")
                | Customer.name.ilike(f"%{query}%")
                | Customer.phone.ilike(f"%{query}%")
            )

        stmt = stmt.order_by(Order.created_at.desc()).limit(10)
        result = await db.execute(stmt)
        orders = result.scalars().all()

        if not orders:
            return "কোনো অর্ডার পাওয়া যায়নি।"

        lines = []
        for o in orders:
            customer_name = o.customer.name if o.customer else "অজানা"
            lines.append(
                f"• {o.order_number} | {customer_name} | ৳{o.total_amount:,.0f} | {o.status.value}"
            )
        return "\n".join(lines)

    @tool
    async def get_order_details(order_number: str) -> str:
        """Get full details for a specific order by order number."""
        from app.models.order import OrderItem

        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.customer),
            )
            .where(
                Order.merchant_id == merchant_id,
                Order.order_number == order_number.upper(),
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            return f"অর্ডার {order_number} পাওয়া যায়নি।"

        customer_info = (
            f"{order.customer.name} ({order.customer.phone})"
            if order.customer
            else "অজানা"
        )

        items_text = "\n".join(
            f"  - {item.product_name} × {item.quantity} = ৳{item.total_price:,.0f}"
            for item in order.items
        )

        return (
            f"অর্ডার: {order.order_number}\n"
            f"কাস্টমার: {customer_info}\n"
            f"স্ট্যাটাস: {order.status.value}\n"
            f"মোট: ৳{order.total_amount:,.0f}\n"
            f"পেমেন্ট: {order.payment_status.value}\n"
            f"পণ্য:\n{items_text}\n"
            f"ঠিকানা: {order.delivery_address or 'উল্লেখ নেই'}"
        )

    return [search_orders, get_order_details]
