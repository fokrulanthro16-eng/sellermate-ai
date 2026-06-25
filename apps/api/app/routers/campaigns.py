"""
Campaigns router — generate and manage marketing campaigns.
"""
from fastapi import APIRouter, Query

from sqlalchemy import select, delete

from app.ai.commerce.campaign_engine import generate_campaign
from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import NotFoundException
from app.models.campaign import Campaign
from app.schemas.commerce import CampaignGenerateRequest, CampaignOut
from app.schemas.common import MessageResponse, SuccessResponse

router = APIRouter(tags=["campaigns"])


@router.get("", response_model=SuccessResponse[list[CampaignOut]])
async def list_campaigns(
    merchant: CurrentMerchant,
    db: DB,
    campaign_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    stmt = (
        select(Campaign)
        .where(Campaign.merchant_id == merchant.id)
        .order_by(Campaign.created_at.desc())
        .limit(limit)
    )
    if campaign_type:
        stmt = stmt.where(Campaign.campaign_type == campaign_type)
    rows = await db.execute(stmt)
    items = rows.scalars().all()
    return SuccessResponse(data=[_to_out(c) for c in items])


@router.post("", response_model=SuccessResponse[CampaignOut])
async def generate_campaign_endpoint(
    payload: CampaignGenerateRequest,
    merchant: CurrentMerchant,
    db: DB,
):
    content, provider_name = await generate_campaign(
        campaign_type=payload.campaign_type,
        product_name=payload.product_name,
        product_price=payload.product_price,
        language=payload.language,
        tone=payload.tone,
        extra_context=payload.extra_context,
    )
    type_labels = {
        "fb_post": "Facebook Post",
        "fb_ad": "Facebook Ad",
        "email": "Email Campaign",
        "sms": "SMS Campaign",
    }
    title = f"{type_labels.get(payload.campaign_type, payload.campaign_type)} — {payload.product_name}"

    campaign = Campaign(
        merchant_id=merchant.id,
        title=title,
        campaign_type=payload.campaign_type,
        content=content,
        language=payload.language,
        status="draft",
        provider=provider_name,
        meta_json={"tone": payload.tone, "extra_context": payload.extra_context},
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return SuccessResponse(data=_to_out(campaign))


@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(campaign_id: str, merchant: CurrentMerchant, db: DB):
    row = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.merchant_id == merchant.id)
    )
    campaign = row.scalar_one_or_none()
    if not campaign:
        raise NotFoundException("Campaign not found")
    await db.execute(
        delete(Campaign).where(Campaign.id == campaign_id, Campaign.merchant_id == merchant.id)
    )
    await db.commit()
    return MessageResponse(message="Campaign deleted")


def _to_out(c: Campaign) -> CampaignOut:
    return CampaignOut(
        id=c.id,
        title=c.title,
        campaign_type=c.campaign_type,
        content=c.content,
        language=c.language,
        status=c.status,
        provider=c.provider,
        created_at=c.created_at.isoformat(),
    )
