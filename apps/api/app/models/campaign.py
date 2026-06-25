import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fb_post | fb_ad | email | sms
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="bn", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    merchant: Mapped["Merchant"] = relationship("Merchant")  # type: ignore[name-defined]
