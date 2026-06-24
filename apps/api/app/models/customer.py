import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CustomerSource(str, PyEnum):
    MANUAL = "MANUAL"
    WHATSAPP = "WHATSAPP"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    WALK_IN = "WALK_IN"


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    last_order_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    source: Mapped[CustomerSource] = mapped_column(
        SAEnum(CustomerSource, name="customer_source_enum"),
        default=CustomerSource.MANUAL,
        nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(  # type: ignore[name-defined]
        "Merchant", back_populates="customers"
    )
    orders: Mapped[list["Order"]] = relationship(  # type: ignore[name-defined]
        "Order", back_populates="customer"
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "phone", name="uq_customers_merchant_phone"),
        Index("ix_customers_merchant_id", "merchant_id"),
        Index("ix_customers_merchant_phone", "merchant_id", "phone"),
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id!r} name={self.name!r} phone={self.phone!r}>"
