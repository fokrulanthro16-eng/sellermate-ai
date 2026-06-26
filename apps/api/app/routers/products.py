from fastapi import APIRouter, Query

from app.core.dependencies import CurrentMerchant, DB
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.product import (
    CreateProductRequest,
    CreateVariantRequest,
    ProductFilters,
    ProductOut,
    ProductWithVariants,
    UpdateProductRequest,
    UpdateVariantRequest,
    VariantOut,
)
from app.services import product_service

router = APIRouter(tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductWithVariants])
async def list_products(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    is_active: bool | None = None,
):
    filters = ProductFilters(page=page, limit=limit, category=category, search=search, is_active=is_active)
    return await product_service.list_products(db, merchant.id, filters)


@router.post("", response_model=SuccessResponse[ProductOut], status_code=201)
async def create_product(body: CreateProductRequest, merchant: CurrentMerchant, db: DB):
    product = await product_service.create_product(db, merchant.id, body)
    return SuccessResponse(data=ProductOut.model_validate(product))


@router.get("/categories", response_model=SuccessResponse[list[str]])
async def get_categories(merchant: CurrentMerchant, db: DB):
    categories = await product_service.get_categories(db, merchant.id)
    return SuccessResponse(data=categories)


@router.get("/{product_id}", response_model=SuccessResponse[ProductWithVariants])
async def get_product(product_id: str, merchant: CurrentMerchant, db: DB):
    product = await product_service.get_product(db, merchant.id, product_id)
    return SuccessResponse(data=product)


@router.patch("/{product_id}", response_model=SuccessResponse[ProductOut])
async def update_product(
    product_id: str, body: UpdateProductRequest, merchant: CurrentMerchant, db: DB
):
    product = await product_service.update_product(db, merchant.id, product_id, body)
    return SuccessResponse(data=ProductOut.model_validate(product))


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str, merchant: CurrentMerchant, db: DB):
    await product_service.delete_product(db, merchant.id, product_id)


@router.post("/{product_id}/variants", response_model=SuccessResponse[VariantOut], status_code=201)
async def add_variant(
    product_id: str, body: CreateVariantRequest, merchant: CurrentMerchant, db: DB
):
    variant = await product_service.add_variant(db, merchant.id, product_id, body)
    return SuccessResponse(data=VariantOut.model_validate(variant))


@router.patch("/{product_id}/variants/{variant_id}", response_model=SuccessResponse[VariantOut])
async def update_variant(
    product_id: str,
    variant_id: str,
    body: UpdateVariantRequest,
    merchant: CurrentMerchant,
    db: DB,
):
    variant = await product_service.update_variant(
        db, merchant.id, product_id, variant_id, body
    )
    return SuccessResponse(data=VariantOut.model_validate(variant))


@router.delete("/{product_id}/variants/{variant_id}", status_code=204)
async def delete_variant(
    product_id: str, variant_id: str, merchant: CurrentMerchant, db: DB
):
    await product_service.delete_variant(db, merchant.id, product_id, variant_id)
