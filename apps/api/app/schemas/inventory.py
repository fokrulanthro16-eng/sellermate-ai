from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.inventory import InventoryChangeType


class AdjustmentItem(BaseModel):
    variant_id: str
    quantity_change: int = Field(..., description="Positive to add, negative to remove; cannot be zero")
    reason: str | None = Field(None, max_length=500)
    type: InventoryChangeType = InventoryChangeType.ADJUSTMENT

    @field_validator("quantity_change")
    @classmethod
    def must_not_be_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("quantity_change cannot be zero")
        return v


class BulkAdjustmentRequest(BaseModel):
    adjustments: list[AdjustmentItem] = Field(..., min_length=1)


class InventoryLogOut(BaseModel):
    id: str
    merchant_id: str
    variant_id: str
    type: InventoryChangeType
    quantity_before: int
    quantity_change: int
    quantity_after: int
    reason: str | None
    reference_id: str | None
    reference_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VariantStockOut(BaseModel):
    variant_id: str
    variant_name: str
    product_id: str
    product_name: str
    sku: str | None
    stock_quantity: int
    low_stock_alert: int
    is_low_stock: bool

    model_config = {"from_attributes": True}


class InventoryFilters(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    low_stock: bool | None = None
    variant_id: str | None = None


class LogFilters(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=200)
    variant_id: str | None = None
    type: InventoryChangeType | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
