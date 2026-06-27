import csv
import io
import math
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.customer import Customer
from app.models.order import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.models.product import Product, ProductVariant
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.order import (
    ChangeStatusRequest,
    CreateOrderRequest,
    OrderFilters,
    OrderWithDetails,
    RecordPaymentRequest,
    UpdateOrderRequest,
)
from app.services import inventory_service


async def list_orders(
    db: AsyncSession, merchant_id: str, filters: OrderFilters
) -> PaginatedResponse:
    query = select(Order).where(Order.merchant_id == merchant_id)

    if filters.status:
        query = query.where(Order.status == filters.status)
    if filters.channel:
        query = query.where(Order.channel == filters.channel)
    if filters.payment_status:
        query = query.where(Order.payment_status == filters.payment_status)
    if filters.from_date:
        query = query.where(Order.created_at >= filters.from_date)
    if filters.to_date:
        query = query.where(Order.created_at <= filters.to_date)
    if filters.search:
        term = f"%{filters.search}%"
        query = query.join(Customer).where(
            or_(
                Order.order_number.ilike(term),
                Customer.name.ilike(term),
                Customer.phone.ilike(term),
            )
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.limit
    result = await db.execute(
        query.order_by(Order.created_at.desc()).offset(offset).limit(filters.limit)
    )
    orders = result.scalars().all()

    from app.schemas.order import OrderOut
    return PaginatedResponse(
        data=[OrderOut.model_validate(o) for o in orders],
        meta=PaginatedMeta(
            page=filters.page,
            limit=filters.limit,
            total=total,
            total_pages=math.ceil(total / filters.limit) if total > 0 else 0,
        ),
    )


async def create_order(
    db: AsyncSession, merchant_id: str, data: CreateOrderRequest
) -> Order:
    # Validate customer belongs to this merchant
    cust_result = await db.execute(
        select(Customer).where(
            Customer.id == data.customer_id, Customer.merchant_id == merchant_id
        )
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer not found")

    # Resolve products and validate stock
    resolved: list[tuple[Product, ProductVariant | None, int]] = []
    for item in data.items:
        prod_result = await db.execute(
            select(Product).where(
                Product.id == item.product_id,
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
            )
        )
        product = prod_result.scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Product {item.product_id} not found")

        variant: ProductVariant | None = None
        if item.variant_id:
            var_result = await db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id,
                    ProductVariant.product_id == product.id,
                )
            )
            variant = var_result.scalar_one_or_none()
            if not variant:
                raise NotFoundException(f"Variant {item.variant_id} not found")
            if variant.stock_quantity < item.quantity:
                raise BadRequestException(
                    f"Insufficient stock for '{product.name}' — "
                    f"{variant.stock_quantity} available, {item.quantity} requested"
                )
        else:
            # Variant-id omitted: reject if the product has variants so stock
            # is never silently skipped during deduction.
            has_variants = (
                await db.execute(
                    select(func.count())
                    .select_from(ProductVariant)
                    .where(ProductVariant.product_id == product.id)
                )
            ).scalar_one() > 0
            if has_variants:
                raise BadRequestException(
                    f"variant_id is required for '{product.name}' — "
                    "product has variants and stock is tracked per variant"
                )

        resolved.append((product, variant, item.quantity))

    # Calculate totals using Decimal to avoid float precision errors
    subtotal = sum(
        (v.price if v and v.price else p.sale_price or p.base_price) * qty
        for p, v, qty in resolved
    )
    total = subtotal - data.discount_amount + data.shipping_cost

    # Generate order number
    order_number = await _generate_order_number(db, merchant_id)

    order = Order(
        merchant_id=merchant_id,
        customer_id=data.customer_id,
        order_number=order_number,
        channel=data.channel,
        subtotal=subtotal,
        discount_amount=data.discount_amount,
        shipping_cost=data.shipping_cost,
        total_amount=total,
        paid_amount=0,
        due_amount=total,
        payment_method=data.payment_method,
        delivery_address=data.delivery_address,
        delivery_district=data.delivery_district,
        delivery_division=data.delivery_division,
        notes=data.notes,
    )
    db.add(order)
    await db.flush()

    for product, variant, qty in resolved:
        unit_price = variant.price if variant and variant.price else product.sale_price or product.base_price
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                product_name=product.name,
                variant_name=variant.name if variant else None,
                quantity=qty,
                unit_price=unit_price,
                total_price=unit_price * qty,
            )
        )

    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PENDING))
    await db.flush()

    # Deduct inventory
    items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    await inventory_service.deduct_for_order(
        db, merchant_id, order.id, list(items_result.scalars().all())
    )

    # Update customer stats
    customer.total_orders += 1
    customer.total_spent = Decimal(str(customer.total_spent)) + total
    customer.last_order_at = datetime.now(UTC)

    return order


async def get_order(
    db: AsyncSession, merchant_id: str, order_id: str
) -> OrderWithDetails:
    result = await db.execute(
        select(Order)
        .where(Order.merchant_id == merchant_id, Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.status_history),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    return OrderWithDetails.model_validate(order)


async def update_order(
    db: AsyncSession, merchant_id: str, order_id: str, data: UpdateOrderRequest
) -> Order:
    result = await db.execute(
        select(Order).where(Order.merchant_id == merchant_id, Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(order, field, value)
    return order


_TERMINAL_STATUSES = {OrderStatus.CANCELLED, OrderStatus.RETURNED}


async def change_status(
    db: AsyncSession, merchant_id: str, order_id: str, req: ChangeStatusRequest
) -> Order:
    result = await db.execute(
        select(Order).where(Order.merchant_id == merchant_id, Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")

    if order.status in _TERMINAL_STATUSES:
        raise BadRequestException(
            f"Cannot change status of a {order.status} order"
        )

    order.status = req.status
    if req.status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.now(UTC)

    db.add(OrderStatusHistory(order_id=order.id, status=req.status, note=req.note))
    return order


async def record_payment(
    db: AsyncSession, merchant_id: str, order_id: str, req: RecordPaymentRequest
) -> Order:
    result = await db.execute(
        select(Order).where(Order.merchant_id == merchant_id, Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")

    if order.status == OrderStatus.CANCELLED:
        raise BadRequestException("Cannot record payment for a cancelled order")

    new_paid = Decimal(str(order.paid_amount)) + req.amount
    if new_paid > order.total_amount:
        raise BadRequestException("Payment exceeds order total")

    order.paid_amount = new_paid
    order.due_amount = order.total_amount - new_paid
    order.payment_method = req.method

    if order.due_amount <= 0:
        order.payment_status = PaymentStatus.PAID
    elif new_paid > 0:
        order.payment_status = PaymentStatus.PARTIAL

    return order


async def cancel_order(db: AsyncSession, merchant_id: str, order_id: str) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.merchant_id == merchant_id, Order.id == order_id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
        raise BadRequestException("Only PENDING or CONFIRMED orders can be cancelled")

    order.status = OrderStatus.CANCELLED
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.CANCELLED))

    # Restore inventory for all items that had stock deducted
    await inventory_service.restore_for_cancelled_order(
        db, merchant_id, order.id, list(order.items)
    )

    # Rollback customer aggregate stats
    cust_result = await db.execute(
        select(Customer).where(Customer.id == order.customer_id)
    )
    customer = cust_result.scalar_one_or_none()
    if customer:
        customer.total_orders = max(0, customer.total_orders - 1)
        customer.total_spent = max(
            Decimal("0"),
            Decimal(str(customer.total_spent)) - Decimal(str(order.total_amount)),
        )

    # Refresh to populate server-side updated_at before Pydantic serialisation
    await db.refresh(order)
    return order


async def export_csv(db: AsyncSession, merchant_id: str, filters: OrderFilters) -> bytes:
    filters.page = 1
    filters.limit = 5000
    page = await list_orders(db, merchant_id, filters)

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "order_number", "status", "channel", "customer_id",
            "total_amount", "paid_amount", "due_amount",
            "payment_method", "payment_status", "created_at",
        ],
    )
    writer.writeheader()
    for order in page.data:
        writer.writerow(order.model_dump(include=set(writer.fieldnames)))

    return buffer.getvalue().encode("utf-8-sig")


async def _generate_order_number(db: AsyncSession, merchant_id: str) -> str:
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(Order.merchant_id == merchant_id)
    )
    count = count_result.scalar_one() + 1
    return f"SM-{date_str}-{count:04d}"
