"""add campaigns table

Revision ID: e71a2b3c4d5e
Revises: d60fe5a071c5
Create Date: 2026-06-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "e71a2b3c4d5e"
down_revision = "d60fe5a071c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("merchant_id", sa.String(36), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("campaign_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="bn"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("provider", sa.String(50), nullable=False, server_default="mock"),
        sa.Column("meta_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_campaigns_merchant_id", "campaigns", ["merchant_id"])
    op.create_index("ix_campaigns_campaign_type", "campaigns", ["campaign_type"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_campaign_type", table_name="campaigns")
    op.drop_index("ix_campaigns_merchant_id", table_name="campaigns")
    op.drop_table("campaigns")
