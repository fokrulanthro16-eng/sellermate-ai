"""add store slug, description, banner, geolocation to merchants

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-25 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("store_slug", sa.String(100), nullable=True))
    op.add_column("merchants", sa.Column("store_description", sa.Text, nullable=True))
    op.add_column("merchants", sa.Column("store_banner_url", sa.String(500), nullable=True))
    op.add_column("merchants", sa.Column("latitude", sa.Float, nullable=True))
    op.add_column("merchants", sa.Column("longitude", sa.Float, nullable=True))
    op.create_unique_constraint("uq_merchants_store_slug", "merchants", ["store_slug"])
    op.create_index("ix_merchants_store_slug", "merchants", ["store_slug"])
    op.create_index("ix_merchants_location", "merchants", ["latitude", "longitude"])


def downgrade() -> None:
    op.drop_index("ix_merchants_location", table_name="merchants")
    op.drop_index("ix_merchants_store_slug", table_name="merchants")
    op.drop_constraint("uq_merchants_store_slug", "merchants", type_="unique")
    op.drop_column("merchants", "longitude")
    op.drop_column("merchants", "latitude")
    op.drop_column("merchants", "store_banner_url")
    op.drop_column("merchants", "store_description")
    op.drop_column("merchants", "store_slug")
