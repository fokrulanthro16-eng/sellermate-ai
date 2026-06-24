import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InventoryChangeType(str, PyEnum):
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    SALE = "SALE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGE = "DAMAGE"


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[InventoryChangeType] = mapped_column(
        SAEnum(InventoryChangeType, name="inventory_change_type_enum"), nullable=False
    )
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    variant: Mapped["ProductVariant"] = relationship(  # type: ignore[name-defined]
        "ProductVariant", back_populates="inventory_logs"
    )

    __table_args__ = (
        Index("ix_inventory_logs_merchant_id", "merchant_id"),
        Index("ix_inventory_logs_variant_id", "variant_id"),
        Index("ix_inventory_logs_merchant_created", "merchant_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<InventoryLog id={self.id!r} type={self.type} "
            f"change={self.quantity_change:+d}>"
        )
