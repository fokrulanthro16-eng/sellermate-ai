from datetime import datetime

from pydantic import BaseModel

from app.models.hermit import InsightSeverity, InsightType


class HermitInsightOut(BaseModel):
    id: str
    merchant_id: str
    insight_type: InsightType
    severity: InsightSeverity
    title: str
    body: str
    meta: dict
    is_read: bool
    expires_at: datetime | None
    generated_at: datetime

    model_config = {"from_attributes": True}


class HermitRunResult(BaseModel):
    insights_generated: int
    insights_cleared: int
    breakdown: dict[str, int]
    run_at: datetime
