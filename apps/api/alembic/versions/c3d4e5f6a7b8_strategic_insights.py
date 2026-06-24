"""strategic insights table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategic_insights",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("agent_name", sa.String(64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
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
        "ix_strategic_insights_merchant_id", "strategic_insights", ["merchant_id"]
    )
    op.create_index(
        "ix_strategic_insights_agent", "strategic_insights", ["merchant_id", "agent_name"]
    )
    op.create_index(
        "ix_strategic_insights_created",
        "strategic_insights",
        ["merchant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_strategic_insights_created", table_name="strategic_insights")
    op.drop_index("ix_strategic_insights_agent", table_name="strategic_insights")
    op.drop_index("ix_strategic_insights_merchant_id", table_name="strategic_insights")
    op.drop_table("strategic_insights")
