from fastapi import APIRouter, Query

from app.core.dependencies import CurrentMerchant, DB
from app.models.hermit import InsightSeverity, InsightType
from app.schemas.common import SuccessResponse
from app.schemas.hermit import HermitInsightOut, HermitRunResult
from app.services import hermit_service

router = APIRouter(prefix="/hermit", tags=["hermit"])


@router.post("/run", response_model=SuccessResponse[HermitRunResult])
async def run_hermit(merchant: CurrentMerchant, db: DB):
    result = await hermit_service.run_analysis(db, merchant.id)
    return SuccessResponse(data=HermitRunResult(**result))


@router.get("/insights", response_model=SuccessResponse[list[HermitInsightOut]])
async def get_insights(
    merchant: CurrentMerchant,
    db: DB,
    insight_type: InsightType | None = Query(None),
    severity: InsightSeverity | None = Query(None),
    unread_only: bool = Query(False),
):
    insights = await hermit_service.get_insights(
        db, merchant.id, insight_type, severity, unread_only
    )
    return SuccessResponse(data=[HermitInsightOut.model_validate(i) for i in insights])


@router.patch("/insights/{insight_id}/read", response_model=SuccessResponse[dict])
async def mark_insight_read(insight_id: str, merchant: CurrentMerchant, db: DB):
    from app.core.exceptions import NotFoundException
    found = await hermit_service.mark_read(db, merchant.id, insight_id)
    if not found:
        raise NotFoundException("Insight not found")
    return SuccessResponse(data={"marked_read": True})
