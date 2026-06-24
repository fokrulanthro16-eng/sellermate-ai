from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderChannel, OrderStatus, PaymentMethod, PaymentStatus


class OrderItemRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity: int = Field(..., ge=1)


class CreateOrderRequest(BaseModel):
    customer_id: str
    channel: OrderChannel = OrderChannel.MANUAL
    items: list[OrderItemRequest] = Field(..., min_length=1)
    discount_amount: Decimal = Field(Decimal("0"), ge=0)
    shipping_cost: Decimal = Field(Decimal("0"), ge=0)
    payment_method: PaymentMethod = PaymentMethod.COD
    delivery_address: str | None = None
    delivery_district: str | None = None
    delivery_division: str | None = None
    notes: str | None = None


class UpdateOrderRequest(BaseModel):
    delivery_address: str | None = None
    delivery_district: str | None = None
    delivery_division: str | None = None
    courier_name: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    internal_notes: str | None = None


class ChangeStatusRequest(BaseModel):
    status: OrderStatus
    note: str | None = None


class RecordPaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: PaymentMethod


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    variant_id: str | None
    product_name: str
    variant_name: str | None
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    id: str
    status: OrderStatus
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    order_number: str
    status: OrderStatus
    channel: OrderChannel
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    due_amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    delivery_address: str | None
    delivery_district: str | None
    delivery_division: str | None
    courier_name: str | None
    tracking_number: str | None
    notes: str | None
    internal_notes: str | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderWithDetails(OrderOut):
    items: list[OrderItemOut] = []
    status_history: list[StatusHistoryOut] = []


class OrderFilters(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    status: OrderStatus | None = None
    channel: OrderChannel | None = None
    payment_status: PaymentStatus | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    search: str | None = None
