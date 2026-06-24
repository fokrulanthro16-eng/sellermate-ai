"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── merchants ─────────────────────────────────────────────────────────────
    # Enum types are created automatically by SQLAlchemy DDL when first referenced.
    op.create_table(
        "merchants",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("owner_name", sa.String(255), nullable=False),
        sa.Column(
            "business_type",
            sa.Enum(
                "FASHION_CLOTHING", "ELECTRONICS", "FOOD_BEVERAGE", "HOME_DECOR",
                "BEAUTY_COSMETICS", "BOOKS_STATIONERY", "HANDICRAFTS", "AGRICULTURE", "OTHER",
                name="business_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("division", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("whatsapp_phone", sa.String(20), nullable=True),
        sa.Column("whatsapp_connected", sa.Boolean(), nullable=False),
        sa.Column("trust_score", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "SUSPENDED", "PENDING_VERIFICATION",
                name="merchant_status_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "plan",
            sa.Enum("FREE", "STARTER", "PRO", name="subscription_plan_enum"),
            nullable=False,
        ),
        sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("onboarding_step", sa.Integer(), nullable=False),
        sa.Column("onboarding_done", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_merchants_email"),
        sa.UniqueConstraint("phone", name="uq_merchants_phone"),
    )

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_bangla", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_bangla", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("sale_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("image_urls", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("total_sold", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "sku", name="uq_products_merchant_sku"),
    )
    op.create_index("ix_products_merchant_id", "products", ["merchant_id"])
    op.create_index("ix_products_merchant_category", "products", ["merchant_id", "category"])

    # ── product_variants ──────────────────────────────────────────────────────
    op.create_table(
        "product_variants",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("low_stock_alert", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    # ── inventory_logs ────────────────────────────────────────────────────────
    op.create_table(
        "inventory_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("variant_id", sa.String(36), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "STOCK_IN", "STOCK_OUT", "SALE", "RETURN", "ADJUSTMENT", "DAMAGE",
                name="inventory_change_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("quantity_before", sa.Integer(), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("reference_id", sa.String(36), nullable=True),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_logs_merchant_id", "inventory_logs", ["merchant_id"])
    op.create_index("ix_inventory_logs_variant_id", "inventory_logs", ["variant_id"])
    op.create_index(
        "ix_inventory_logs_merchant_created", "inventory_logs", ["merchant_id", "created_at"]
    )

    # ── customers ─────────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("division", sa.String(100), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("total_orders", sa.Integer(), nullable=False),
        sa.Column("total_spent", sa.Numeric(14, 2), nullable=False),
        sa.Column("last_order_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "MANUAL", "WHATSAPP", "FACEBOOK", "INSTAGRAM", "WALK_IN",
                name="customer_source_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "phone", name="uq_customers_merchant_phone"),
    )
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])
    op.create_index("ix_customers_merchant_phone", "customers", ["merchant_id", "phone"])

    # ── orders ────────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("customer_id", sa.String(36), nullable=False),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "CONFIRMED", "PROCESSING", "SHIPPED",
                "DELIVERED", "CANCELLED", "RETURNED",
                name="order_status_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum(
                "MANUAL", "WHATSAPP", "FACEBOOK", "INSTAGRAM", "WEBSITE",
                name="order_channel_enum",
            ),
            nullable=False,
        ),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "payment_method",
            sa.Enum(
                "COD", "BKASH", "NAGAD", "ROCKET", "BANK_TRANSFER", "CARD",
                name="payment_method_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "UNPAID", "PARTIAL", "PAID", "REFUNDED",
                name="payment_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("delivery_address", sa.String(500), nullable=True),
        sa.Column("delivery_district", sa.String(100), nullable=True),
        sa.Column("delivery_division", sa.String(100), nullable=True),
        sa.Column("courier_name", sa.String(100), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index("ix_orders_merchant_id", "orders", ["merchant_id"])
    op.create_index("ix_orders_merchant_status", "orders", ["merchant_id", "status"])
    op.create_index("ix_orders_merchant_created", "orders", ["merchant_id", "created_at"])
    op.create_index("ix_orders_order_number", "orders", ["order_number"])

    # ── order_items ───────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("variant_id", sa.String(36), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("variant_name", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    # ── order_status_history ──────────────────────────────────────────────────
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "CONFIRMED", "PROCESSING", "SHIPPED",
                "DELIVERED", "CANCELLED", "RETURNED",
                name="order_status_enum", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_order_status_history_order_id", "order_status_history", ["order_id"]
    )

    # ── conversations ─────────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_merchant_id", "conversations", ["merchant_id"])

    # ── messages ──────────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column(
            "role",
            sa.Enum("USER", "ASSISTANT", "SYSTEM", name="message_role_enum"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_results", sa.JSON(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_merchant_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_order_status_history_order_id", table_name="order_status_history")
    op.drop_table("order_status_history")

    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_index("ix_orders_merchant_created", table_name="orders")
    op.drop_index("ix_orders_merchant_status", table_name="orders")
    op.drop_index("ix_orders_merchant_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_customers_merchant_phone", table_name="customers")
    op.drop_index("ix_customers_merchant_id", table_name="customers")
    op.drop_table("customers")

    op.drop_index("ix_inventory_logs_merchant_created", table_name="inventory_logs")
    op.drop_index("ix_inventory_logs_variant_id", table_name="inventory_logs")
    op.drop_index("ix_inventory_logs_merchant_id", table_name="inventory_logs")
    op.drop_table("inventory_logs")

    op.drop_index("ix_product_variants_product_id", table_name="product_variants")
    op.drop_table("product_variants")

    op.drop_index("ix_products_merchant_category", table_name="products")
    op.drop_index("ix_products_merchant_id", table_name="products")
    op.drop_table("products")

    op.drop_table("merchants")

    # Drop enum types (reverse creation order)
    op.execute(sa.text("DROP TYPE IF EXISTS message_role_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS payment_status_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS payment_method_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS order_channel_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS order_status_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS customer_source_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS inventory_change_type_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS subscription_plan_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS merchant_status_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS business_type_enum"))
