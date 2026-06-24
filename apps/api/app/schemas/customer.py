import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.customer import CustomerSource

_BD_PHONE_RE = re.compile(r"^\+8801[3-9]\d{8}$")


class CreateCustomerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., examples=["+8801712345678"])
    email: str | None = None
    address: str | None = Field(None, max_length=500)
    district: str | None = Field(None, max_length=100)
    division: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)
    tags: list[str] = Field(default_factory=list)
    source: CustomerSource = CustomerSource.MANUAL

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not _BD_PHONE_RE.match(v):
            raise ValueError("Must be a valid Bangladeshi mobile number (+8801XXXXXXXXX)")
        return v


class UpdateCustomerRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = None
    address: str | None = Field(None, max_length=500)
    district: str | None = Field(None, max_length=100)
    division: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)


class CustomerOut(BaseModel):
    id: str
    merchant_id: str
    name: str
    phone: str
    email: str | None
    address: str | None
    district: str | None
    division: str | None
    notes: str | None
    total_orders: int
    total_spent: Decimal
    last_order_at: datetime | None
    tags: list[str]
    source: CustomerSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerFilters(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    search: str | None = None
    district: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: CustomerSource | None = None
