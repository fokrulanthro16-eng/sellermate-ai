import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InsightType(str, PyEnum):
    SLOW_MOVING_PRODUCT  = "SLOW_MOVING_PRODUCT"
    LOW_STOCK            = "LOW_STOCK"
    REPEAT_BUYER         = "REPEAT_BUYER"
    UNUSUAL_ORDER_PATTERN = "UNUSUAL_ORDER_PATTERN"
    WEEKLY_HEALTH        = "WEEKLY_HEALTH"


class InsightSeverity(str, PyEnum):
    INFO     = "INFO"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


class HermitInsight(Base):
    """Silent background intelligence record — never surfaces automatically."""

    __tablename__ = "hermit_insights"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    insight_type: Mapped[InsightType] = mapped_column(
        SAEnum(InsightType, name="insight_type_enum"), nullable=False
    )
    severity: Mapped[InsightSeverity] = mapped_column(
        SAEnum(InsightSeverity, name="insight_severity_enum"),
        default=InsightSeverity.INFO,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_hermit_insights_merchant_id", "merchant_id"),
        Index("ix_hermit_insights_type",       "merchant_id", "insight_type"),
        Index("ix_hermit_insights_generated",  "merchant_id", "generated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<HermitInsight id={self.id!r} type={self.insight_type.value} "
            f"severity={self.severity.value}>"
        )
