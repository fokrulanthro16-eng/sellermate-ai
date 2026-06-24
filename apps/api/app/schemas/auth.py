import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.merchant import BusinessType, MerchantStatus, SubscriptionPlan

_BD_PHONE_RE = re.compile(r"^\+8801[3-9]\d{8}$")


def _validate_bd_phone(v: str) -> str:
    if not _BD_PHONE_RE.match(v):
        raise ValueError("Must be a valid Bangladeshi mobile number (+8801XXXXXXXXX)")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., examples=["+8801712345678"])
    password: str = Field(..., min_length=8, max_length=128)
    business_name: str = Field(..., min_length=2, max_length=255)
    owner_name: str = Field(..., min_length=2, max_length=255)
    business_type: BusinessType

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_bd_phone(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or phone number")
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_bd_phone(v)


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_bd_phone(v)


class ResetPasswordRequest(BaseModel):
    phone: str
    otp: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_bd_phone(v)


class MerchantOut(BaseModel):
    id: str
    email: str
    phone: str
    business_name: str
    owner_name: str
    business_type: BusinessType
    address: str | None
    district: str | None
    division: str | None
    logo_url: str | None
    whatsapp_phone: str | None
    whatsapp_connected: bool
    trust_score: int
    status: MerchantStatus
    plan: SubscriptionPlan
    plan_expires_at: datetime | None
    onboarding_step: int
    onboarding_done: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    merchant: MerchantOut
    tokens: TokenPair
