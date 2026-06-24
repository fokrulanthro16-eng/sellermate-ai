from langchain_core.tools import tool
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductVariant


def make_product_tools(db: AsyncSession, merchant_id: str):
    @tool
    async def search_products(query: str) -> str:
        """Search products by name, Bangla name, or SKU."""
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.variants))
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.name_bangla.ilike(f"%{query}%"),
                    Product.sku.ilike(f"%{query}%"),
                ),
            )
            .limit(10)
        )
        products = result.scalars().all()

        if not products:
            return f'"{query}" নামে কোনো পণ্য পাওয়া যায়নি।'

        lines = []
        for p in products:
            total_stock = sum(v.stock_quantity for v in p.variants)
            variant_count = len(p.variants)
            price_display = (
                f"৳{p.base_price:,.0f}"
                if p.base_price
                else "ভেরিয়েন্ট অনুযায়ী"
            )
            lines.append(
                f"• {p.name} ({p.name_bangla or '—'}) | {price_display} | "
                f"{variant_count}টি ভেরিয়েন্ট | মোট স্টক: {total_stock}"
            )
        return "\n".join(lines)

    @tool
    async def get_product_variants(product_name: str) -> str:
        """Get all variants and their stock for a product."""
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.variants))
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
                or_(
                    Product.name.ilike(f"%{product_name}%"),
                    Product.name_bangla.ilike(f"%{product_name}%"),
                ),
            )
            .limit(1)
        )
        product = result.scalar_one_or_none()
        if not product:
            return f'"{product_name}" নামে কোনো পণ্য পাওয়া যায়নি।'

        lines = [f"পণ্য: {product.name}"]
        for v in product.variants:
            stock_status = (
                "স্টক শেষ" if v.stock_quantity == 0
                else f"{v.stock_quantity} পিস"
            )
            lines.append(f"  • {v.name} | ৳{v.price:,.0f} | {stock_status}")
        return "\n".join(lines)

    return [search_products, get_product_variants]
