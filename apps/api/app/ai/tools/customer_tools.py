from langchain_core.tools import tool
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


def make_customer_tools(db: AsyncSession, merchant_id: str):
    @tool
    async def search_customers(query: str) -> str:
        """Search customers by name or phone number."""
        result = await db.execute(
            select(Customer)
            .where(
                Customer.merchant_id == merchant_id,
                or_(
                    Customer.name.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%"),
                ),
            )
            .limit(10)
        )
        customers = result.scalars().all()

        if not customers:
            return f'"{query}" নামে কোনো কাস্টমার পাওয়া যায়নি।'

        lines = []
        for c in customers:
            lines.append(
                f"• {c.name} | {c.phone} | মোট অর্ডার: {c.total_orders} | মোট কেনাকাটা: ৳{c.total_spent:,.0f}"
            )
        return "\n".join(lines)

    @tool
    async def get_customer_by_phone(phone: str) -> str:
        """Look up a specific customer by their phone number."""
        result = await db.execute(
            select(Customer).where(
                Customer.merchant_id == merchant_id,
                Customer.phone == phone,
            )
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return f"ফোন নম্বর {phone} দিয়ে কোনো কাস্টমার পাওয়া যায়নি।"

        tags_text = ", ".join(customer.tags) if customer.tags else "কোনো ট্যাগ নেই"
        return (
            f"নাম: {customer.name}\n"
            f"ফোন: {customer.phone}\n"
            f"ঠিকানা: {customer.address or 'উল্লেখ নেই'}\n"
            f"মোট অর্ডার: {customer.total_orders}টি\n"
            f"মোট কেনাকাটা: ৳{customer.total_spent:,.0f}\n"
            f"ট্যাগ: {tags_text}"
        )

    return [search_customers, get_customer_by_phone]
