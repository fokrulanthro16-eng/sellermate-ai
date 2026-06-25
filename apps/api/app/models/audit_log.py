"""Audit log — immutable record of every significant data-changing action."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)       # create | update | delete | status_change | export | login | logout
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False) # order | product | customer | payment | courier | settings
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    resource_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_audit_logs_merchant_id", "merchant_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
