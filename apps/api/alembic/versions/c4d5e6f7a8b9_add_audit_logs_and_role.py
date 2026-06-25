"""add audit_logs table and merchant role

Revision ID: c4d5e6f7a8b9
Revises: f82c9d0e1b2a
Create Date: 2026-06-25 06:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "f82c9d0e1b2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to merchants
    merchant_role_enum = sa.Enum("OWNER", "ADMIN", "STAFF", "VIEWER", name="merchant_role_enum")
    merchant_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("merchants", sa.Column("role", merchant_role_enum, nullable=False, server_default="OWNER"))

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("resource_label", sa.String(255), nullable=False, server_default=""),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_merchant_id", "audit_logs", ["merchant_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_merchant_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_column("merchants", "role")
    sa.Enum(name="merchant_role_enum").drop(op.get_bind(), checkfirst=True)
