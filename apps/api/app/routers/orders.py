from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.core.dependencies import CurrentMerchant, DB
from app.models.order import OrderChannel, OrderStatus, PaymentStatus
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.order import (
    ChangeStatusRequest,
    CreateOrderRequest,
    OrderFilters,
    OrderOut,
    OrderWithDetails,
    RecordPaymentRequest,
    UpdateOrderRequest,
)
from app.services import order_service

router = APIRouter(tags=["orders"])


@router.get("", response_model=PaginatedResponse[OrderOut])
async def list_orders(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = None,
    channel: OrderChannel | None = None,
    payment_status: PaymentStatus | None = None,
    search: str | None = None,
):
    filters = OrderFilters(
        page=page, limit=limit, status=status, channel=channel,
        payment_status=payment_status, search=search,
    )
    return await order_service.list_orders(db, merchant.id, filters)


@router.post("", response_model=SuccessResponse[OrderOut], status_code=201)
async def create_order(body: CreateOrderRequest, merchant: CurrentMerchant, db: DB):
    order = await order_service.create_order(db, merchant.id, body)
    return SuccessResponse(data=OrderOut.model_validate(order))


@router.get("/export")
async def export_orders(
    merchant: CurrentMerchant,
    db: DB,
    status: OrderStatus | None = None,
):
    filters = OrderFilters(page=1, status=status)  # limit overridden in export_csv
    csv_bytes = await order_service.export_csv(db, merchant.id, filters)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/{order_id}", response_model=SuccessResponse[OrderWithDetails])
async def get_order(order_id: str, merchant: CurrentMerchant, db: DB):
    order = await order_service.get_order(db, merchant.id, order_id)
    return SuccessResponse(data=order)


@router.patch("/{order_id}", response_model=SuccessResponse[OrderOut])
async def update_order(
    order_id: str, body: UpdateOrderRequest, merchant: CurrentMerchant, db: DB
):
    order = await order_service.update_order(db, merchant.id, order_id, body)
    return SuccessResponse(data=OrderOut.model_validate(order))


@router.post("/{order_id}/status", response_model=SuccessResponse[OrderOut])
async def change_status(
    order_id: str, body: ChangeStatusRequest, merchant: CurrentMerchant, db: DB
):
    order = await order_service.change_status(db, merchant.id, order_id, body)
    return SuccessResponse(data=OrderOut.model_validate(order))


@router.post("/{order_id}/payment", response_model=SuccessResponse[OrderOut])
async def record_payment(
    order_id: str, body: RecordPaymentRequest, merchant: CurrentMerchant, db: DB
):
    order = await order_service.record_payment(db, merchant.id, order_id, body)
    return SuccessResponse(data=OrderOut.model_validate(order))


@router.delete("/{order_id}", response_model=SuccessResponse[OrderOut])
async def cancel_order(order_id: str, merchant: CurrentMerchant, db: DB):
    order = await order_service.cancel_order(db, merchant.id, order_id)
    return SuccessResponse(data=OrderOut.model_validate(order))
