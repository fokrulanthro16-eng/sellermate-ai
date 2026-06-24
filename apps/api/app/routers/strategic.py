from fastapi import APIRouter, Query

from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import NotFoundException
from app.schemas.common import SuccessResponse
from app.schemas.strategic import (
    FraudReportOut,
    StrategicInsightOut,
    StrategicRunResult,
    StrategicSummaryOut,
    TrustScoreOut,
)
from app.services import strategic_service

router = APIRouter(tags=["strategic"])


@router.post("/run", response_model=SuccessResponse[StrategicRunResult], status_code=200)
async def run_strategic_agents(merchant: CurrentMerchant, db: DB):
    result = await strategic_service.run_agents(db, merchant.id)
    return SuccessResponse(data=result)


@router.get("/insights", response_model=SuccessResponse[list[StrategicInsightOut]])
async def list_insights(
    merchant: CurrentMerchant,
    db: DB,
    agent_name: str | None = Query(None, description="trust_graph | fraud_sentinel"),
    limit: int = Query(20, ge=1, le=100),
):
    insights = await strategic_service.get_insights(db, merchant.id, agent_name, limit)
    return SuccessResponse(data=insights)


@router.get("/trust-score", response_model=SuccessResponse[StrategicInsightOut])
async def get_trust_score(merchant: CurrentMerchant, db: DB):
    insight = await strategic_service.get_latest_trust(db, merchant.id)
    if not insight:
        raise NotFoundException("No trust score available — run /strategic/run first")
    return SuccessResponse(data=insight)


@router.get("/fraud-report", response_model=SuccessResponse[StrategicInsightOut])
async def get_fraud_report(merchant: CurrentMerchant, db: DB):
    insight = await strategic_service.get_latest_fraud(db, merchant.id)
    if not insight:
        raise NotFoundException("No fraud report available — run /strategic/run first")
    return SuccessResponse(data=insight)


@router.get("/summary", response_model=SuccessResponse[StrategicSummaryOut])
async def get_strategic_summary(merchant: CurrentMerchant, db: DB):
    summary = await strategic_service.get_summary(db, merchant.id)
    return SuccessResponse(data=summary)
