from pydantic import BaseModel, Field

from app.models.merchant import BusinessType


class UpdateMerchantRequest(BaseModel):
    business_name: str | None = Field(None, min_length=2, max_length=255)
    owner_name: str | None = Field(None, min_length=2, max_length=255)
    business_type: BusinessType | None = None
    address: str | None = Field(None, max_length=500)
    district: str | None = Field(None, max_length=100)
    division: str | None = Field(None, max_length=100)
    whatsapp_phone: str | None = Field(None, max_length=20)


class OnboardingStepRequest(BaseModel):
    step: int = Field(..., ge=1, le=5)
    data: dict


class DashboardStats(BaseModel):
    today_revenue: float
    today_orders: int
    pending_orders: int
    low_stock_variants: int
    new_customers_today: int
    revenue_change_pct: float
    orders_change_pct: float


class WhatsAppStatus(BaseModel):
    connected: bool
    phone: str | None
    qr_code: str | None = None
