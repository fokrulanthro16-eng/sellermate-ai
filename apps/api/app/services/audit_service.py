"""Audit service — call log_action() from any router to record an event."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    merchant_id: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    resource_label: str = "",
    details: dict[str, Any] | None = None,
    actor_id: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        merchant_id=merchant_id,
        actor_id=actor_id or merchant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_label=resource_label,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    return entry
