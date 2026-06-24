from pydantic import BaseModel


class TrustScoreOut(BaseModel):
    trust_score: int
    confidence: str
    risk_flags: list[str]
    positive_signals: list[str] = []
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class FraudReportOut(BaseModel):
    fraud_risk_score: int
    risk_level: str = "LOW"
    alert_reasons: list[str]
    suspicious_patterns: list[str] = []
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class GrowthCoachOut(BaseModel):
    growth_score: int
    trend_direction: str
    revenue_growth_pct: float
    retention_rate: float
    top_product_concentration: float
    recommendations: list[str] = []
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class MarginGuardianOut(BaseModel):
    margin_score: int
    risk_level: str
    cod_ratio: float
    refund_rate: float
    avg_discount_rate: float
    unpaid_exposure: float
    flags: list[str] = []
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class DemandOracleOut(BaseModel):
    restock_score: int
    critical_count: int
    high_count: int
    total_sku_tracked: int
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class CreditReadinessOut(BaseModel):
    credit_score: int
    eligibility: str
    revenue_consistency: float
    payment_collection_rate: float
    cancellation_rate: float
    monthly_revenue_avg: float
    credit_limit_estimate: float
    improvement_tips: list[str] = []
    explanation_bn: str = ""
    explanation_en: str = ""
    details: dict


class StrategicRunResult(BaseModel):
    trust: TrustScoreOut
    fraud: FraudReportOut
    growth: GrowthCoachOut | None = None
    margin: MarginGuardianOut | None = None
    demand: DemandOracleOut | None = None
    credit: CreditReadinessOut | None = None
    insights_saved: int


class StrategicInsightOut(BaseModel):
    id: str
    agent_name: str
    score: int
    payload: dict
    created_at: str

    model_config = {"from_attributes": True}


class StrategicSummaryOut(BaseModel):
    trust_score: int
    fraud_score: int
    risk_level: str
    top_insights: list[str]
    explanation_bn: str
    explanation_en: str
