from langchain_core.tools import tool
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductVariant


def make_inventory_tools(db: AsyncSession, merchant_id: str):
    @tool
    async def check_stock(product_name: str) -> str:
        """Check current stock levels for a product by name."""
        result = await db.execute(
            select(ProductVariant)
            .join(Product)
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
                or_(
                    Product.name.ilike(f"%{product_name}%"),
                    Product.name_bangla.ilike(f"%{product_name}%"),
                ),
            )
        )
        variants = result.scalars().all()

        if not variants:
            return f'"{product_name}" নামে কোনো পণ্য পাওয়া যায়নি।'

        lines = []
        for v in variants:
            status = (
                "স্টক শেষ ⚠️" if v.stock_quantity == 0
                else "কম স্টক ⚠️" if v.stock_quantity <= v.low_stock_alert
                else "স্টক আছে ✓"
            )
            lines.append(f"• {v.name}: {v.stock_quantity} পিস — {status}")

        return "\n".join(lines)

    @tool
    async def adjust_stock(variant_id: str, quantity_change: int, reason: str = "") -> str:
        """
        Add or remove stock for a specific variant.
        quantity_change: positive to add, negative to remove.
        """
        result = await db.execute(
            select(ProductVariant)
            .join(Product)
            .where(
                Product.merchant_id == merchant_id,
                ProductVariant.id == variant_id,
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            return "ভেরিয়েন্ট পাওয়া যায়নি।"

        new_qty = variant.stock_quantity + quantity_change
        if new_qty < 0:
            return (
                f"স্টক কমানো সম্ভব নয়। "
                f"বর্তমান স্টক: {variant.stock_quantity} পিস।"
            )

        from app.models.inventory import InventoryChangeType, InventoryLog

        log = InventoryLog(
            merchant_id=merchant_id,
            variant_id=variant.id,
            type=InventoryChangeType.ADJUSTMENT,
            quantity_before=variant.stock_quantity,
            quantity_change=quantity_change,
            quantity_after=new_qty,
            reason=reason or "AI দ্বারা আপডেট",
            reference_type="AI",
        )
        db.add(log)
        variant.stock_quantity = new_qty
        await db.flush()

        return f"স্টক আপডেট ✓ {variant.name}: {variant.stock_quantity - quantity_change} → {new_qty} পিস"

    return [check_stock, adjust_stock]
