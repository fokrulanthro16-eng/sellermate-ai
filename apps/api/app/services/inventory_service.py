import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.inventory import InventoryChangeType, InventoryLog
from app.models.order import OrderItem
from app.models.product import Product, ProductVariant
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.inventory import (
    AdjustmentItem,
    BulkAdjustmentRequest,
    InventoryFilters,
    InventoryLogOut,
    LogFilters,
    VariantStockOut,
)


async def list_stock(
    db: AsyncSession, merchant_id: str, filters: InventoryFilters
) -> PaginatedResponse:
    query = (
        select(ProductVariant)
        .join(Product)
        .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
        .options(selectinload(ProductVariant.product))
    )

    if filters.low_stock:
        query = query.where(
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert
        )
    if filters.variant_id:
        query = query.where(ProductVariant.id == filters.variant_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.limit
    result = await db.execute(
        query.order_by(ProductVariant.id).offset(offset).limit(filters.limit)
    )
    variants = result.scalars().all()

    data = [
        VariantStockOut(
            variant_id=v.id,
            variant_name=v.name,
            product_id=v.product_id,
            product_name=v.product.name,
            sku=v.sku,
            stock_quantity=v.stock_quantity,
            low_stock_alert=v.low_stock_alert,
            is_low_stock=v.stock_quantity <= v.low_stock_alert,
        )
        for v in variants
    ]

    return PaginatedResponse(
        data=data,
        meta=PaginatedMeta(
            page=filters.page,
            limit=filters.limit,
            total=total,
            total_pages=math.ceil(total / filters.limit) if total > 0 else 0,
        ),
    )


async def adjust(
    db: AsyncSession, merchant_id: str, req: BulkAdjustmentRequest
) -> list[InventoryLog]:
    logs: list[InventoryLog] = []

    for item in req.adjustments:
        result = await db.execute(
            select(ProductVariant)
            .join(Product)
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
                ProductVariant.id == item.variant_id,
            )
            .with_for_update()
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise NotFoundException(f"Variant {item.variant_id} not found")

        new_qty = variant.stock_quantity + item.quantity_change
        if new_qty < 0:
            raise BadRequestException(
                f"Cannot reduce stock below 0 for variant '{variant.name}' "
                f"(current: {variant.stock_quantity})"
            )

        log = InventoryLog(
            merchant_id=merchant_id,
            variant_id=variant.id,
            type=item.type,
            quantity_before=variant.stock_quantity,
            quantity_change=item.quantity_change,
            quantity_after=new_qty,
            reason=item.reason,
            reference_type="ADJUSTMENT",
        )
        db.add(log)
        variant.stock_quantity = new_qty
        logs.append(log)

    await db.flush()
    return logs


async def get_logs(
    db: AsyncSession, merchant_id: str, filters: LogFilters
) -> PaginatedResponse:
    query = select(InventoryLog).where(InventoryLog.merchant_id == merchant_id)

    if filters.variant_id:
        query = query.where(InventoryLog.variant_id == filters.variant_id)
    if filters.type:
        query = query.where(InventoryLog.type == filters.type)
    if filters.from_date:
        query = query.where(InventoryLog.created_at >= filters.from_date)
    if filters.to_date:
        query = query.where(InventoryLog.created_at <= filters.to_date)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.limit
    result = await db.execute(
        query.order_by(InventoryLog.created_at.desc()).offset(offset).limit(filters.limit)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        data=[InventoryLogOut.model_validate(log) for log in logs],
        meta=PaginatedMeta(
            page=filters.page,
            limit=filters.limit,
            total=total,
            total_pages=math.ceil(total / filters.limit) if total > 0 else 0,
        ),
    )


async def get_low_stock_alerts(db: AsyncSession, merchant_id: str) -> list[VariantStockOut]:
    result = await db.execute(
        select(ProductVariant)
        .join(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
        )
        .options(selectinload(ProductVariant.product))
        .order_by(ProductVariant.stock_quantity.asc())
    )
    variants = result.scalars().all()

    return [
        VariantStockOut(
            variant_id=v.id,
            variant_name=v.name,
            product_id=v.product_id,
            product_name=v.product.name,
            sku=v.sku,
            stock_quantity=v.stock_quantity,
            low_stock_alert=v.low_stock_alert,
            is_low_stock=True,
        )
        for v in variants
    ]


async def deduct_for_order(
    db: AsyncSession, merchant_id: str, order_id: str, items: list[OrderItem]
) -> None:
    for item in items:
        if not item.variant_id:
            continue
        result = await db.execute(
            select(ProductVariant)
            .join(Product)
            .where(
                ProductVariant.id == item.variant_id,
                Product.merchant_id == merchant_id,
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            continue

        new_qty = max(0, variant.stock_quantity - item.quantity)
        log = InventoryLog(
            merchant_id=merchant_id,
            variant_id=variant.id,
            type=InventoryChangeType.SALE,
            quantity_before=variant.stock_quantity,
            quantity_change=-item.quantity,
            quantity_after=new_qty,
            reference_id=order_id,
            reference_type="ORDER",
        )
        db.add(log)
        variant.stock_quantity = new_qty


async def restore_for_cancelled_order(
    db: AsyncSession, merchant_id: str, order_id: str, items: list[OrderItem]
) -> None:
    for item in items:
        if not item.variant_id:
            continue
        result = await db.execute(
            select(ProductVariant)
            .join(Product)
            .where(
                ProductVariant.id == item.variant_id,
                Product.merchant_id == merchant_id,
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            continue

        new_qty = variant.stock_quantity + item.quantity
        log = InventoryLog(
            merchant_id=merchant_id,
            variant_id=variant.id,
            type=InventoryChangeType.RETURN,
            quantity_before=variant.stock_quantity,
            quantity_change=item.quantity,
            quantity_after=new_qty,
            reference_id=order_id,
            reference_type="ORDER_CANCEL",
        )
        db.add(log)
        variant.stock_quantity = new_qty
