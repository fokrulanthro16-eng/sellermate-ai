"""add webhook_events and background_jobs tables

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-25 08:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("signature", sa.String(512), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_webhook_events_provider", "webhook_events", ["provider"])
    op.create_index("ix_webhook_events_status", "webhook_events", ["status"])
    op.create_index("ix_webhook_events_received_at", "webhook_events", ["received_at"])

    op.create_table(
        "background_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("merchant_id", sa.String(36), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("result", sa.JSON, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_background_jobs_merchant_id", "background_jobs", ["merchant_id"])
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])
    op.create_index("ix_background_jobs_created_at", "background_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_background_jobs_created_at", table_name="background_jobs")
    op.drop_index("ix_background_jobs_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_merchant_id", table_name="background_jobs")
    op.drop_table("background_jobs")

    op.drop_index("ix_webhook_events_received_at", table_name="webhook_events")
    op.drop_index("ix_webhook_events_status", table_name="webhook_events")
    op.drop_index("ix_webhook_events_provider", table_name="webhook_events")
    op.drop_table("webhook_events")
