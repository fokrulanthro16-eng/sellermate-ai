from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.strategic_agents.fraud_sentinel import FraudSentinel
from app.ai.strategic_agents.trust_graph import TrustGraph
from app.models.strategic_insight import StrategicInsight
from app.schemas.strategic import (
    FraudReportOut,
    StrategicInsightOut,
    StrategicRunResult,
    TrustScoreOut,
)


async def run_agents(db: AsyncSession, merchant_id: str) -> StrategicRunResult:
    trust_result = await TrustGraph().run(db, merchant_id)
    fraud_result = await FraudSentinel().run(db, merchant_id)

    trust_payload = asdict(trust_result)
    fraud_payload = asdict(fraud_result)

    trust_record = StrategicInsight(
        merchant_id=merchant_id,
        agent_name="trust_graph",
        score=trust_result.trust_score,
        payload=trust_payload,
    )
    fraud_record = StrategicInsight(
        merchant_id=merchant_id,
        agent_name="fraud_sentinel",
        score=fraud_result.fraud_risk_score,
        payload=fraud_payload,
    )
    db.add(trust_record)
    db.add(fraud_record)
    await db.flush()

    return StrategicRunResult(
        trust=TrustScoreOut(
            trust_score=trust_result.trust_score,
            confidence=trust_result.confidence,
            risk_flags=trust_result.risk_flags,
            details=trust_result.details,
        ),
        fraud=FraudReportOut(
            fraud_risk_score=fraud_result.fraud_risk_score,
            alert_reasons=fraud_result.alert_reasons,
            details=fraud_result.details,
        ),
        insights_saved=2,
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
        id=row.id,
        agent_name=row.agent_name,
        score=row.score,
        payload=row.payload,
        created_at=str(row.created_at),
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
        id=row.id,
        agent_name=row.agent_name,
        score=row.score,
        payload=row.payload,
        created_at=str(row.created_at),
    )
