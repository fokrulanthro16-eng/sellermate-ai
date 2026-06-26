import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MerchantRole(str, PyEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    VIEWER = "VIEWER"


class BusinessType(str, PyEnum):
    FASHION_CLOTHING = "FASHION_CLOTHING"
    ELECTRONICS = "ELECTRONICS"
    FOOD_BEVERAGE = "FOOD_BEVERAGE"
    HOME_DECOR = "HOME_DECOR"
    BEAUTY_COSMETICS = "BEAUTY_COSMETICS"
    BOOKS_STATIONERY = "BOOKS_STATIONERY"
    HANDICRAFTS = "HANDICRAFTS"
    AGRICULTURE = "AGRICULTURE"
    OTHER = "OTHER"


class MerchantStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class SubscriptionPlan(str, PyEnum):
    FREE = "FREE"
    STARTER = "STARTER"
    PRO = "PRO"


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[BusinessType] = mapped_column(
        SAEnum(BusinessType, name="business_type_enum"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    status: Mapped[MerchantStatus] = mapped_column(
        SAEnum(MerchantStatus, name="merchant_status_enum"),
        default=MerchantStatus.ACTIVE,
        nullable=False,
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(
        SAEnum(SubscriptionPlan, name="subscription_plan_enum"),
        default=SubscriptionPlan.FREE,
        nullable=False,
    )
    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[MerchantRole] = mapped_column(
        SAEnum(MerchantRole, name="merchant_role_enum"),
        default=MerchantRole.OWNER,
        nullable=False,
    )

    # Public storefront fields (Phase 9)
    store_slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    store_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    products: Mapped[list["Product"]] = relationship(  # type: ignore[name-defined]
        "Product", back_populates="merchant", cascade="all, delete-orphan"
    )
    customers: Mapped[list["Customer"]] = relationship(  # type: ignore[name-defined]
        "Customer", back_populates="merchant", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(  # type: ignore[name-defined]
        "Order", back_populates="merchant", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # type: ignore[name-defined]
        "Conversation", back_populates="merchant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_merchants_email"),
        UniqueConstraint("phone", name="uq_merchants_phone"),
        Index("ix_merchants_store_slug", "store_slug"),
        Index("ix_merchants_location", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Merchant id={self.id!r} business={self.business_name!r}>"
