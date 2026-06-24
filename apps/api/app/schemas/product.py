from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class VariantAttributeMap(BaseModel):
    model_config = {"extra": "allow"}


class CreateVariantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    attributes: dict = Field(default_factory=dict)
    sku: str | None = Field(None, max_length=100)
    price: Decimal | None = Field(None, gt=0)
    stock_quantity: int = Field(0, ge=0)
    low_stock_alert: int = Field(5, ge=0)
    image_url: str | None = None


class UpdateVariantRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    attributes: dict | None = None
    sku: str | None = Field(None, max_length=100)
    price: Decimal | None = Field(None, gt=0)
    stock_quantity: int | None = Field(None, ge=0)
    low_stock_alert: int | None = Field(None, ge=0)
    image_url: str | None = None


class VariantOut(BaseModel):
    id: str
    product_id: str
    name: str
    attributes: dict
    sku: str | None
    price: Decimal | None
    stock_quantity: int
    low_stock_alert: int
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    name_bangla: str | None = Field(None, max_length=255)
    description: str | None = None
    description_bangla: str | None = None
    category: str = Field(..., min_length=1, max_length=100)
    sku: str | None = Field(None, max_length=100)
    base_price: Decimal = Field(..., gt=0)
    sale_price: Decimal | None = Field(None, gt=0)
    is_active: bool = True
    variants: list[CreateVariantRequest] = Field(default_factory=list)


class UpdateProductRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    name_bangla: str | None = Field(None, max_length=255)
    description: str | None = None
    description_bangla: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    sku: str | None = Field(None, max_length=100)
    base_price: Decimal | None = Field(None, gt=0)
    sale_price: Decimal | None = Field(None, gt=0)
    is_active: bool | None = None
    is_published: bool | None = None


class ProductOut(BaseModel):
    id: str
    merchant_id: str
    name: str
    name_bangla: str | None
    description: str | None
    description_bangla: str | None
    category: str
    sku: str | None
    base_price: Decimal
    sale_price: Decimal | None
    image_urls: list[str]
    is_active: bool
    is_published: bool
    total_sold: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductWithVariants(ProductOut):
    variants: list[VariantOut] = []


class ProductFilters(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    category: str | None = None
    search: str | None = None
    is_active: bool | None = None
