"""Audit logs router — read-only activity timeline."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select, func

from app.core.dependencies import CurrentMerchant, DB
from app.models.audit_log import AuditLog

router = APIRouter(tags=["audit"])


@router.get("")
async def list_audit_logs(
    merchant: CurrentMerchant,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    resource_type: str | None = Query(None),
    action: str | None = Query(None),
) -> dict:
    q = select(AuditLog).where(AuditLog.merchant_id == merchant.id)
    if resource_type:
        q = q.where(AuditLog.resource_type == resource_type)
    if action:
        q = q.where(AuditLog.action == action)
    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)

    count_q = select(func.count()).select_from(AuditLog).where(AuditLog.merchant_id == merchant.id)
    if resource_type:
        count_q = count_q.where(AuditLog.resource_type == resource_type)
    if action:
        count_q = count_q.where(AuditLog.action == action)

    rows = (await db.execute(q)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0

    return {
        "success": True,
        "data": {
            "logs": [
                {
                    "id": r.id,
                    "action": r.action,
                    "resource_type": r.resource_type,
                    "resource_id": r.resource_id,
                    "resource_label": r.resource_label,
                    "details": r.details,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@router.get("/summary")
async def audit_summary(merchant: CurrentMerchant, db: DB) -> dict:
    q = select(AuditLog.action, func.count().label("count")).where(
        AuditLog.merchant_id == merchant.id
    ).group_by(AuditLog.action)
    rows = (await db.execute(q)).all()
    return {"success": True, "data": {r.action: r.count for r in rows}}
