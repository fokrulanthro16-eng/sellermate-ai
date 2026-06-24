from fastapi import APIRouter

from app.core.dependencies import CurrentMerchant, DB
from app.schemas.auth import MerchantOut
from app.schemas.common import SuccessResponse
from app.schemas.merchant import (
    DashboardStats,
    OnboardingStepRequest,
    UpdateMerchantRequest,
    WhatsAppStatus,
)
from app.services import merchant_service

router = APIRouter(tags=["merchant"])


@router.get("/me", response_model=SuccessResponse[MerchantOut])
async def get_profile(merchant: CurrentMerchant):
    return SuccessResponse(data=MerchantOut.model_validate(merchant))


@router.patch("/me", response_model=SuccessResponse[MerchantOut])
async def update_profile(body: UpdateMerchantRequest, merchant: CurrentMerchant, db: DB):
    updated = await merchant_service.update(db, merchant.id, body)
    return SuccessResponse(data=MerchantOut.model_validate(updated))


@router.post("/onboarding", response_model=SuccessResponse[MerchantOut])
async def complete_onboarding_step(
    body: OnboardingStepRequest, merchant: CurrentMerchant, db: DB
):
    updated = await merchant_service.complete_onboarding_step(db, merchant.id, body)
    return SuccessResponse(data=MerchantOut.model_validate(updated))


@router.get("/stats", response_model=SuccessResponse[DashboardStats])
async def dashboard_stats(merchant: CurrentMerchant, db: DB):
    stats = await merchant_service.get_dashboard_stats(db, merchant.id)
    return SuccessResponse(data=stats)


@router.post("/whatsapp/connect", response_model=SuccessResponse[WhatsAppStatus])
async def connect_whatsapp(merchant: CurrentMerchant):
    # Placeholder — WhatsApp QR flow requires BSP integration
    return SuccessResponse(
        data=WhatsAppStatus(
            connected=merchant.whatsapp_connected,
            phone=merchant.whatsapp_phone,
            qr_code=None,
        )
    )


@router.get("/whatsapp/status", response_model=SuccessResponse[WhatsAppStatus])
async def whatsapp_status(merchant: CurrentMerchant):
    return SuccessResponse(
        data=WhatsAppStatus(
            connected=merchant.whatsapp_connected,
            phone=merchant.whatsapp_phone,
        )
    )
