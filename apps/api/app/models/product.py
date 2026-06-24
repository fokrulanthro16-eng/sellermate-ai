import uuid
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_bangla: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bangla: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_urls: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="products")  # type: ignore[name-defined]
    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )
    order_items: Mapped[list["OrderItem"]] = relationship(  # type: ignore[name-defined]
        "OrderItem", back_populates="product"
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "sku", name="uq_products_merchant_sku"),
        Index("ix_products_merchant_id", "merchant_id"),
        Index("ix_products_merchant_category", "merchant_id", "category"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id!r} name={self.name!r}>"


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_alert: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    inventory_logs: Mapped[list["InventoryLog"]] = relationship(  # type: ignore[name-defined]
        "InventoryLog", back_populates="variant"
    )
    order_items: Mapped[list["OrderItem"]] = relationship(  # type: ignore[name-defined]
        "OrderItem", back_populates="variant"
    )

    __table_args__ = (Index("ix_product_variants_product_id", "product_id"),)

    def __repr__(self) -> str:
        return f"<ProductVariant id={self.id!r} name={self.name!r} stock={self.stock_quantity}>"
