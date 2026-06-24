from fastapi import APIRouter, Query

from app.core.dependencies import CurrentMerchant, DB
from app.models.inventory import InventoryChangeType
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.inventory import (
    BulkAdjustmentRequest,
    InventoryFilters,
    InventoryLogOut,
    LogFilters,
    VariantStockOut,
)
from app.services import inventory_service

router = APIRouter(tags=["inventory"])


@router.get("", response_model=PaginatedResponse[VariantStockOut])
async def list_stock(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    low_stock: bool | None = None,
    variant_id: str | None = None,
):
    filters = InventoryFilters(page=page, limit=limit, low_stock=low_stock, variant_id=variant_id)
    return await inventory_service.list_stock(db, merchant.id, filters)


@router.post("/adjust", response_model=SuccessResponse[list[InventoryLogOut]])
async def adjust(body: BulkAdjustmentRequest, merchant: CurrentMerchant, db: DB):
    logs = await inventory_service.adjust(db, merchant.id, body)
    return SuccessResponse(data=[InventoryLogOut.model_validate(log) for log in logs])


@router.get("/alerts", response_model=SuccessResponse[list[VariantStockOut]])
async def low_stock_alerts(merchant: CurrentMerchant, db: DB):
    items = await inventory_service.get_low_stock_alerts(db, merchant.id)
    return SuccessResponse(data=items)


@router.get("/logs", response_model=PaginatedResponse[InventoryLogOut])
async def get_logs(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    variant_id: str | None = None,
    type: InventoryChangeType | None = None,
):
    filters = LogFilters(page=page, limit=limit, variant_id=variant_id, type=type)
    return await inventory_service.get_logs(db, merchant.id, filters)
