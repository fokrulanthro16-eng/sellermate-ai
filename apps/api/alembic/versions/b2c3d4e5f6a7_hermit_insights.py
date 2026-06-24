"""hermit insights table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-21 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hermit_insights",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column(
            "insight_type",
            sa.Enum(
                "SLOW_MOVING_PRODUCT",
                "LOW_STOCK",
                "REPEAT_BUYER",
                "UNUSUAL_ORDER_PATTERN",
                "WEEKLY_HEALTH",
                name="insight_type_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("INFO", "WARNING", "CRITICAL", name="insight_severity_enum"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"], ["merchants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hermit_insights_merchant_id", "hermit_insights", ["merchant_id"]
    )
    op.create_index(
        "ix_hermit_insights_type", "hermit_insights", ["merchant_id", "insight_type"]
    )
    op.create_index(
        "ix_hermit_insights_generated",
        "hermit_insights",
        ["merchant_id", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_hermit_insights_generated", table_name="hermit_insights")
    op.drop_index("ix_hermit_insights_type", table_name="hermit_insights")
    op.drop_index("ix_hermit_insights_merchant_id", table_name="hermit_insights")
    op.drop_table("hermit_insights")
    op.execute("DROP TYPE IF EXISTS insight_type_enum")
    op.execute("DROP TYPE IF EXISTS insight_severity_enum")
