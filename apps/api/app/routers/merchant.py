from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.dependencies import CurrentMerchant, DB
from app.models.order import Order
from app.models.product import Product
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


@router.get("/launch-checklist")
async def launch_checklist(merchant: CurrentMerchant, db: DB) -> dict:
    """Return seller launch readiness checklist."""
    product_count_r = await db.execute(
        select(func.count()).where(Product.merchant_id == merchant.id, Product.is_active.is_(True))
    )
    product_count = product_count_r.scalar() or 0

    order_count_r = await db.execute(
        select(func.count()).where(Order.merchant_id == merchant.id)
    )
    order_count = order_count_r.scalar() or 0

    items = [
        {
            "id": "profile",
            "label": "Profile complete",
            "done": bool(merchant.owner_name and merchant.district and merchant.address),
        },
        {
            "id": "store_live",
            "label": "Public store live",
            "done": bool(merchant.store_slug),
        },
        {
            "id": "products",
            "label": "Products added",
            "done": product_count >= 1,
            "detail": f"{product_count} product(s) added",
        },
        {
            "id": "payment",
            "label": "Payment method configured",
            "done": bool(merchant.whatsapp_phone),
            "detail": "Link payment via Integrations",
        },
        {
            "id": "delivery",
            "label": "Delivery method selected",
            "done": bool(merchant.district),
            "detail": "Set in Integrations > Courier",
        },
        {
            "id": "first_order",
            "label": "First order received",
            "done": order_count >= 1,
            "detail": f"{order_count} order(s) total",
        },
    ]

    done = sum(1 for i in items if i["done"])
    return {
        "success": True,
        "data": {
            "items": items,
            "done": done,
            "total": len(items),
            "pct": round(done / len(items) * 100),
        },
    }
