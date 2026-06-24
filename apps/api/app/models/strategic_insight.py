import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StrategicInsight(Base):
    __tablename__ = "strategic_insights"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_strategic_insights_merchant_id", "merchant_id"),
        Index("ix_strategic_insights_agent", "merchant_id", "agent_name"),
        Index("ix_strategic_insights_created", "merchant_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<StrategicInsight agent={self.agent_name!r} score={self.score}>"
