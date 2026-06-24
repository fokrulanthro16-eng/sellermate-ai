from pydantic import BaseModel


class TrustScoreOut(BaseModel):
    trust_score: int
    confidence: str
    risk_flags: list[str]
    details: dict


class FraudReportOut(BaseModel):
    fraud_risk_score: int
    alert_reasons: list[str]
    details: dict


class StrategicRunResult(BaseModel):
    trust: TrustScoreOut
    fraud: FraudReportOut
    insights_saved: int


class StrategicInsightOut(BaseModel):
    id: str
    agent_name: str
    score: int
    payload: dict
    created_at: str

    model_config = {"from_attributes": True}
