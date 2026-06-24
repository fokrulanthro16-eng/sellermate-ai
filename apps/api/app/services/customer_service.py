import csv
import io
import math

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.customer import (
    CreateCustomerRequest,
    CustomerFilters,
    CustomerOut,
    UpdateCustomerRequest,
)


async def list_customers(
    db: AsyncSession, merchant_id: str, filters: CustomerFilters
) -> PaginatedResponse:
    query = select(Customer).where(Customer.merchant_id == merchant_id)

    if filters.search:
        term = f"%{filters.search}%"
        query = query.where(
            or_(Customer.name.ilike(term), Customer.phone.ilike(term))
        )
    if filters.district:
        query = query.where(Customer.district == filters.district)
    if filters.source:
        query = query.where(Customer.source == filters.source)
    if filters.tags:
        for tag in filters.tags:
            query = query.where(Customer.tags.any(tag))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.limit
    result = await db.execute(
        query.order_by(Customer.total_spent.desc(), Customer.id).offset(offset).limit(filters.limit)
    )
    customers = result.scalars().all()

    return PaginatedResponse(
        data=[CustomerOut.model_validate(c) for c in customers],
        meta=PaginatedMeta(
            page=filters.page,
            limit=filters.limit,
            total=total,
            total_pages=math.ceil(total / filters.limit) if total > 0 else 0,
        ),
    )


async def create_customer(
    db: AsyncSession, merchant_id: str, data: CreateCustomerRequest
) -> Customer:
    existing = await db.execute(
        select(Customer).where(
            Customer.merchant_id == merchant_id, Customer.phone == data.phone
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("A customer with this phone number already exists")

    customer = Customer(merchant_id=merchant_id, **data.model_dump())
    db.add(customer)
    await db.flush()
    return customer


async def get_customer(
    db: AsyncSession, merchant_id: str, customer_id: str
) -> Customer:
    result = await db.execute(
        select(Customer).where(
            Customer.merchant_id == merchant_id, Customer.id == customer_id
        )
    )
    customer = result.scalar_one_or_none()
    # Defensive: re-verify after fetch because identity-map caching can return
    # an object with a different merchant_id than what was queried.
    if not customer or str(customer.merchant_id) != str(merchant_id):
        raise NotFoundException("Customer not found")
    return customer


async def find_by_phone(
    db: AsyncSession, merchant_id: str, phone: str
) -> Customer | None:
    result = await db.execute(
        select(Customer).where(
            Customer.merchant_id == merchant_id, Customer.phone == phone
        )
    )
    return result.scalar_one_or_none()


async def update_customer(
    db: AsyncSession, merchant_id: str, customer_id: str, data: UpdateCustomerRequest
) -> Customer:
    customer = await get_customer(db, merchant_id, customer_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(customer, field, value)
    return customer


async def delete_customer(db: AsyncSession, merchant_id: str, customer_id: str) -> None:
    customer = await get_customer(db, merchant_id, customer_id)

    order_count = await db.execute(
        select(func.count()).where(Order.customer_id == customer_id)
    )
    if order_count.scalar_one() > 0:
        raise BadRequestException("Cannot delete customer with existing orders")

    await db.delete(customer)


async def manage_tags(
    db: AsyncSession,
    merchant_id: str,
    customer_id: str,
    action: str,
    tag: str,
) -> Customer:
    customer = await get_customer(db, merchant_id, customer_id)
    tags = list(customer.tags or [])

    if action == "add":
        if tag not in tags:
            tags.append(tag)
    elif action == "remove":
        tags = [t for t in tags if t != tag]

    customer.tags = tags
    return customer


async def export_csv(db: AsyncSession, merchant_id: str) -> bytes:
    result = await db.execute(
        select(Customer)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.total_spent.desc(), Customer.id)
    )
    customers = result.scalars().all()

    buffer = io.StringIO()
    fields = ["name", "phone", "email", "district", "division", "total_orders", "total_spent", "source"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for c in customers:
        writer.writerow({f: getattr(c, f, "") for f in fields})

    return buffer.getvalue().encode("utf-8-sig")
