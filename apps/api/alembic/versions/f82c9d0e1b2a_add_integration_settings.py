"""add integration settings table

Revision ID: f82c9d0e1b2a
Revises: e71a2b3c4d5e
Create Date: 2026-06-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "f82c9d0e1b2a"
down_revision = "e71a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("merchant_id", sa.String(36), nullable=False, unique=True),
        sa.Column("config_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", name="uq_integration_settings_merchant"),
    )
    op.create_index("ix_integration_settings_merchant_id", "integration_settings", ["merchant_id"])


def downgrade() -> None:
    op.drop_index("ix_integration_settings_merchant_id", table_name="integration_settings")
    op.drop_table("integration_settings")
