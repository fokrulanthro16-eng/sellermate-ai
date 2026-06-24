from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.core.dependencies import CurrentMerchant, DB
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.customer import (
    CreateCustomerRequest,
    CustomerFilters,
    CustomerOut,
    UpdateCustomerRequest,
)
from app.schemas.common import MessageResponse
from app.services import customer_service

router = APIRouter(tags=["customers"])


@router.get("", response_model=PaginatedResponse[CustomerOut])
async def list_customers(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    district: str | None = None,
    source: str | None = None,
    tags: list[str] = Query(default=[]),
):
    filters = CustomerFilters(page=page, limit=limit, search=search, district=district, tags=tags, source=source)
    return await customer_service.list_customers(db, merchant.id, filters)


@router.post("", response_model=SuccessResponse[CustomerOut], status_code=201)
async def create_customer(body: CreateCustomerRequest, merchant: CurrentMerchant, db: DB):
    customer = await customer_service.create_customer(db, merchant.id, body)
    return SuccessResponse(data=CustomerOut.model_validate(customer))


@router.get("/export")
async def export_customers(merchant: CurrentMerchant, db: DB):
    csv_bytes = await customer_service.export_csv(db, merchant.id)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers.csv"},
    )


@router.get("/{customer_id}", response_model=SuccessResponse[CustomerOut])
async def get_customer(customer_id: str, merchant: CurrentMerchant, db: DB):
    customer = await customer_service.get_customer(db, merchant.id, customer_id)
    return SuccessResponse(data=CustomerOut.model_validate(customer))


@router.patch("/{customer_id}", response_model=SuccessResponse[CustomerOut])
async def update_customer(
    customer_id: str, body: UpdateCustomerRequest, merchant: CurrentMerchant, db: DB
):
    customer = await customer_service.update_customer(db, merchant.id, customer_id, body)
    return SuccessResponse(data=CustomerOut.model_validate(customer))


@router.delete("/{customer_id}", response_model=MessageResponse)
async def delete_customer(customer_id: str, merchant: CurrentMerchant, db: DB):
    await customer_service.delete_customer(db, merchant.id, customer_id)
    return MessageResponse(message="Customer deleted")


@router.post("/{customer_id}/tags/{tag}", response_model=SuccessResponse[CustomerOut])
async def add_tag(customer_id: str, tag: str, merchant: CurrentMerchant, db: DB):
    customer = await customer_service.manage_tags(db, merchant.id, customer_id, "add", tag)
    return SuccessResponse(data=CustomerOut.model_validate(customer))


@router.delete("/{customer_id}/tags/{tag}", response_model=SuccessResponse[CustomerOut])
async def remove_tag(customer_id: str, tag: str, merchant: CurrentMerchant, db: DB):
    customer = await customer_service.manage_tags(db, merchant.id, customer_id, "remove", tag)
    return SuccessResponse(data=CustomerOut.model_validate(customer))
