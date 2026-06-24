from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.strategic_agents.credit_readiness import CreditReadiness
from app.ai.strategic_agents.demand_oracle import DemandOracle
from app.ai.strategic_agents.fraud_sentinel import FraudSentinel
from app.ai.strategic_agents.growth_coach import GrowthCoach
from app.ai.strategic_agents.margin_guardian import MarginGuardian
from app.ai.strategic_agents.trust_graph import TrustGraph
from app.models.strategic_insight import StrategicInsight
from app.schemas.strategic import (
    CreditReadinessOut,
    DemandOracleOut,
    FraudReportOut,
    GrowthCoachOut,
    MarginGuardianOut,
    StrategicInsightOut,
    StrategicRunResult,
    StrategicSummaryOut,
    TrustScoreOut,
)


async def run_agents(db: AsyncSession, merchant_id: str) -> StrategicRunResult:
    """Run all 6 strategic agents and persist results to the DB."""

    # ── Run all agents ────────────────────────────────────────
    trust_result  = await TrustGraph().run(db, merchant_id)
    fraud_result  = await FraudSentinel().run(db, merchant_id)
    growth_result = await GrowthCoach().run(db, merchant_id)
    margin_result = await MarginGuardian().run(db, merchant_id)
    demand_result = await DemandOracle().run(db, merchant_id)
    credit_result = await CreditReadiness().run(db, merchant_id)

    # ── Persist all insights ──────────────────────────────────
    records = [
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="trust_graph",
            score=trust_result.trust_score,
            payload=asdict(trust_result),
        ),
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="fraud_sentinel",
            score=fraud_result.fraud_risk_score,
            payload=asdict(fraud_result),
        ),
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="growth_coach",
            score=growth_result.growth_score,
            payload={
                "growth_score": growth_result.growth_score,
                "trend_direction": growth_result.trend_direction,
                "revenue_growth_pct": growth_result.revenue_growth_pct,
                "top_product_concentration": growth_result.top_product_concentration,
                "retention_rate": growth_result.retention_rate,
                "recommendations": growth_result.recommendations,
                "explanation_bn": growth_result.explanation_bn,
                "explanation_en": growth_result.explanation_en,
                **growth_result.details,
            },
        ),
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="margin_guardian",
            score=margin_result.margin_score,
            payload={
                "margin_score": margin_result.margin_score,
                "risk_level": margin_result.risk_level,
                "cod_ratio": margin_result.cod_ratio,
                "refund_rate": margin_result.refund_rate,
                "avg_discount_rate": margin_result.avg_discount_rate,
                "unpaid_exposure": margin_result.unpaid_exposure,
                "flags": margin_result.flags,
                "explanation_bn": margin_result.explanation_bn,
                "explanation_en": margin_result.explanation_en,
                **margin_result.details,
            },
        ),
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="demand_oracle",
            score=demand_result.restock_score,
            payload={
                "restock_score": demand_result.restock_score,
                "critical_count": demand_result.critical_count,
                "high_count": demand_result.high_count,
                "total_sku_tracked": demand_result.total_sku_tracked,
                "explanation_bn": demand_result.explanation_bn,
                "explanation_en": demand_result.explanation_en,
                **demand_result.details,
            },
        ),
        StrategicInsight(
            merchant_id=merchant_id,
            agent_name="credit_readiness",
            score=credit_result.credit_score,
            payload={
                "credit_score": credit_result.credit_score,
                "eligibility": credit_result.eligibility,
                "revenue_consistency": credit_result.revenue_consistency,
                "payment_collection_rate": credit_result.payment_collection_rate,
                "cancellation_rate": credit_result.cancellation_rate,
                "monthly_revenue_avg": credit_result.monthly_revenue_avg,
                "credit_limit_estimate": credit_result.credit_limit_estimate,
                "improvement_tips": credit_result.improvement_tips,
                "explanation_bn": credit_result.explanation_bn,
                "explanation_en": credit_result.explanation_en,
                **credit_result.details,
            },
        ),
    ]
    for rec in records:
        db.add(rec)
    await db.flush()
    await db.commit()

    return StrategicRunResult(
        trust=TrustScoreOut(
            trust_score=trust_result.trust_score,
            confidence=trust_result.confidence,
            risk_flags=trust_result.risk_flags,
            positive_signals=trust_result.positive_signals,
            explanation_bn=trust_result.explanation_bn,
            explanation_en=trust_result.explanation_en,
            details=trust_result.details,
        ),
        fraud=FraudReportOut(
            fraud_risk_score=fraud_result.fraud_risk_score,
            risk_level=fraud_result.risk_level,
            alert_reasons=fraud_result.alert_reasons,
            suspicious_patterns=fraud_result.suspicious_patterns,
            explanation_bn=fraud_result.explanation_bn,
            explanation_en=fraud_result.explanation_en,
            details=fraud_result.details,
        ),
        growth=GrowthCoachOut(
            growth_score=growth_result.growth_score,
            trend_direction=growth_result.trend_direction,
            revenue_growth_pct=growth_result.revenue_growth_pct,
            retention_rate=growth_result.retention_rate,
            top_product_concentration=growth_result.top_product_concentration,
            recommendations=growth_result.recommendations,
            explanation_bn=growth_result.explanation_bn,
            explanation_en=growth_result.explanation_en,
            details=growth_result.details,
        ),
        margin=MarginGuardianOut(
            margin_score=margin_result.margin_score,
            risk_level=margin_result.risk_level,
            cod_ratio=margin_result.cod_ratio,
            refund_rate=margin_result.refund_rate,
            avg_discount_rate=margin_result.avg_discount_rate,
            unpaid_exposure=margin_result.unpaid_exposure,
            flags=margin_result.flags,
            explanation_bn=margin_result.explanation_bn,
            explanation_en=margin_result.explanation_en,
            details=margin_result.details,
        ),
        demand=DemandOracleOut(
            restock_score=demand_result.restock_score,
            critical_count=demand_result.critical_count,
            high_count=demand_result.high_count,
            total_sku_tracked=demand_result.total_sku_tracked,
            explanation_bn=demand_result.explanation_bn,
            explanation_en=demand_result.explanation_en,
            details=demand_result.details,
        ),
        credit=CreditReadinessOut(
            credit_score=credit_result.credit_score,
            eligibility=credit_result.eligibility,
            revenue_consistency=credit_result.revenue_consistency,
            payment_collection_rate=credit_result.payment_collection_rate,
            cancellation_rate=credit_result.cancellation_rate,
            monthly_revenue_avg=credit_result.monthly_revenue_avg,
            credit_limit_estimate=credit_result.credit_limit_estimate,
            improvement_tips=credit_result.improvement_tips,
            explanation_bn=credit_result.explanation_bn,
            explanation_en=credit_result.explanation_en,
            details=credit_result.details,
        ),
        insights_saved=len(records),
    )


async def get_insights(
    db: AsyncSession, merchant_id: str, agent_name: str | None = None, limit: int = 20
) -> list[StrategicInsightOut]:
    q = (
        select(StrategicInsight)
        .where(StrategicInsight.merchant_id == merchant_id)
        .order_by(StrategicInsight.created_at.desc())
        .limit(limit)
    )
    if agent_name:
        q = q.where(StrategicInsight.agent_name == agent_name)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        StrategicInsightOut(
            id=r.id,
            agent_name=r.agent_name,
            score=r.score,
            payload=r.payload,
            created_at=str(r.created_at),
        )
        for r in rows
    ]


async def get_latest_trust(db: AsyncSession, merchant_id: str) -> StrategicInsightOut | None:
    result = await db.execute(
        select(StrategicInsight)
        .where(
            StrategicInsight.merchant_id == merchant_id,
            StrategicInsight.agent_name == "trust_graph",
        )
        .order_by(StrategicInsight.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return StrategicInsightOut(
        id=row.id, agent_name=row.agent_name, score=row.score,
        payload=row.payload, created_at=str(row.created_at),
    )


async def get_latest_fraud(db: AsyncSession, merchant_id: str) -> StrategicInsightOut | None:
    result = await db.execute(
        select(StrategicInsight)
        .where(
            StrategicInsight.merchant_id == merchant_id,
            StrategicInsight.agent_name == "fraud_sentinel",
        )
        .order_by(StrategicInsight.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return StrategicInsightOut(
        id=row.id, agent_name=row.agent_name, score=row.score,
        payload=row.payload, created_at=str(row.created_at),
    )


async def get_summary(db: AsyncSession, merchant_id: str) -> StrategicSummaryOut:
    trust_row = await get_latest_trust(db, merchant_id)
    fraud_row = await get_latest_fraud(db, merchant_id)

    trust_score   = trust_row.score   if trust_row else 0
    fraud_score   = fraud_row.score   if fraud_row else 0
    trust_payload = trust_row.payload if trust_row else {}
    fraud_payload = fraud_row.payload if fraud_row else {}

    risk_level       = fraud_payload.get("risk_level", "LOW")
    risk_flags       = trust_payload.get("risk_flags", [])
    positive_signals = trust_payload.get("positive_signals", [])
    alert_reasons    = fraud_payload.get("alert_reasons", [])

    top_insights: list[str] = []
    for flag   in risk_flags[:2]:      top_insights.append(flag)
    for sig    in positive_signals[:1]: top_insights.append(sig)
    for alert  in alert_reasons[:2]:    top_insights.append(alert.split(":")[0])
    top_insights = top_insights[:3]

    explanation_bn = trust_payload.get("explanation_bn", "এআই এজেন্ট চালান প্রথমে।")
    explanation_en = trust_payload.get("explanation_en", "Run AI agents first to generate insights.")

    return StrategicSummaryOut(
        trust_score=trust_score,
        fraud_score=fraud_score,
        risk_level=risk_level,
        top_insights=top_insights,
        explanation_bn=explanation_bn,
        explanation_en=explanation_en,
    )
