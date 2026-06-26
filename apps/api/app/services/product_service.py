import math

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.product import Product, ProductVariant
from app.schemas.product import (
    CreateProductRequest,
    CreateVariantRequest,
    ProductFilters,
    ProductWithVariants,
    UpdateProductRequest,
    UpdateVariantRequest,
)
from app.schemas.common import PaginatedMeta, PaginatedResponse


async def list_products(
    db: AsyncSession, merchant_id: str, filters: ProductFilters
) -> PaginatedResponse:
    query = select(Product).where(Product.merchant_id == merchant_id)

    if filters.category:
        query = query.where(Product.category == filters.category)
    if filters.is_active is not None:
        query = query.where(Product.is_active == filters.is_active)
    else:
        query = query.where(Product.is_active.is_(True))
    if filters.search:
        term = f"%{filters.search}%"
        query = query.where(
            or_(
                Product.name.ilike(term),
                Product.name_bangla.ilike(term),
                Product.sku.ilike(term),
            )
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.limit
    result = await db.execute(
        query.options(selectinload(Product.variants))
        .order_by(Product.created_at.desc()).offset(offset).limit(filters.limit)
    )
    products = result.scalars().all()

    from app.schemas.product import ProductWithVariants
    return PaginatedResponse(
        data=[ProductWithVariants.model_validate(p) for p in products],
        meta=PaginatedMeta(
            page=filters.page,
            limit=filters.limit,
            total=total,
            total_pages=math.ceil(total / filters.limit) if total > 0 else 0,
        ),
    )


async def create_product(
    db: AsyncSession, merchant_id: str, data: CreateProductRequest
) -> Product:
    if data.sku:
        existing = await db.execute(
            select(Product).where(
                Product.merchant_id == merchant_id, Product.sku == data.sku
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"SKU '{data.sku}' already exists")

    product = Product(
        merchant_id=merchant_id,
        name=data.name,
        name_bangla=data.name_bangla,
        description=data.description,
        description_bangla=data.description_bangla,
        category=data.category,
        sku=data.sku,
        base_price=data.base_price,
        sale_price=data.sale_price,
        is_active=data.is_active,
    )
    db.add(product)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictException(f"SKU '{data.sku}' already exists")

    for v in data.variants:
        variant = ProductVariant(
            product_id=product.id,
            name=v.name,
            attributes=v.attributes,
            sku=v.sku,
            price=v.price,
            stock_quantity=v.stock_quantity,
            low_stock_alert=v.low_stock_alert,
            image_url=v.image_url,
        )
        db.add(variant)

    await db.flush()
    return product


async def get_product(
    db: AsyncSession, merchant_id: str, product_id: str
) -> ProductWithVariants:
    result = await db.execute(
        select(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.id == product_id,
            Product.is_active.is_(True),
        )
        .options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found")
    return ProductWithVariants.model_validate(product)


async def update_product(
    db: AsyncSession, merchant_id: str, product_id: str, data: UpdateProductRequest
) -> Product:
    result = await db.execute(
        select(Product).where(
            Product.merchant_id == merchant_id,
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    return product


async def delete_product(db: AsyncSession, merchant_id: str, product_id: str) -> None:
    result = await db.execute(
        select(Product).where(Product.merchant_id == merchant_id, Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found")
    product.is_active = False


async def add_variant(
    db: AsyncSession, merchant_id: str, product_id: str, data: CreateVariantRequest
) -> ProductVariant:
    result = await db.execute(
        select(Product).where(
            Product.merchant_id == merchant_id,
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Product not found")

    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    await db.flush()
    return variant


async def update_variant(
    db: AsyncSession,
    merchant_id: str,
    product_id: str,
    variant_id: str,
    data: UpdateVariantRequest,
) -> ProductVariant:
    result = await db.execute(
        select(ProductVariant)
        .join(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            ProductVariant.product_id == product_id,
            ProductVariant.id == variant_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundException("Variant not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(variant, field, value)
    return variant


async def delete_variant(
    db: AsyncSession, merchant_id: str, product_id: str, variant_id: str
) -> None:
    result = await db.execute(
        select(ProductVariant)
        .join(Product)
        .where(
            Product.merchant_id == merchant_id,
            Product.is_active.is_(True),
            ProductVariant.product_id == product_id,
            ProductVariant.id == variant_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundException("Variant not found")
    await db.delete(variant)


async def get_categories(db: AsyncSession, merchant_id: str) -> list[str]:
    result = await db.execute(
        select(Product.category)
        .where(Product.merchant_id == merchant_id, Product.is_active.is_(True))
        .distinct()
        .order_by(Product.category)
    )
    return list(result.scalars().all())
