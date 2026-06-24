import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class OrderStatus(str, PyEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class OrderChannel(str, PyEnum):
    MANUAL = "MANUAL"
    WHATSAPP = "WHATSAPP"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    WEBSITE = "WEBSITE"


class PaymentMethod(str, PyEnum):
    COD = "COD"
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    ROCKET = "ROCKET"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"


class PaymentStatus(str, PyEnum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    channel: Mapped[OrderChannel] = mapped_column(
        SAEnum(OrderChannel, name="order_channel_enum"),
        default=OrderChannel.MANUAL,
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    due_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method_enum"),
        default=PaymentMethod.COD,
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.UNPAID,
        nullable=False,
    )
    delivery_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    delivery_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    courier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(  # type: ignore[name-defined]
        "Merchant", back_populates="orders"
    )
    customer: Mapped["Customer"] = relationship(  # type: ignore[name-defined]
        "Customer", back_populates="orders"
    )
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_merchant_id", "merchant_id"),
        Index("ix_orders_merchant_status", "merchant_id", "status"),
        Index("ix_orders_merchant_created", "merchant_id", "created_at"),
        Index("ix_orders_order_number", "order_number"),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id!r} number={self.order_number!r} status={self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id"), nullable=False
    )
    variant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("product_variants.id"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship(  # type: ignore[name-defined]
        "Product", back_populates="order_items"
    )
    variant: Mapped["ProductVariant | None"] = relationship(  # type: ignore[name-defined]
        "ProductVariant", back_populates="order_items"
    )

    __table_args__ = (Index("ix_order_items_order_id", "order_id"),)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")

    __table_args__ = (Index("ix_order_status_history_order_id", "order_id"),)
