"""
Notifications router — computed real-time alerts from live business data.
"""
from fastapi import APIRouter

from app.ai.commerce import CommerceEngine
from app.core.dependencies import CurrentMerchant, DB
from app.schemas.commerce import NotificationOut
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["notifications"])
_engine = CommerceEngine()


@router.get("", response_model=SuccessResponse[list[NotificationOut]])
async def get_notifications(merchant: CurrentMerchant, db: DB):
    data = await _engine.get_notifications(db, merchant.id)
    return SuccessResponse(data=[NotificationOut(**n) for n in data])
