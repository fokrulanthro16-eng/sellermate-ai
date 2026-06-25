"""Background job router — enqueue, status, retry (mock synchronous execution)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, desc, func

from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import NotFoundException
from app.models.background_job import BackgroundJob

router = APIRouter(tags=["jobs"])

_MOCK_HANDLERS: dict[str, object] = {
    "courier_sync": lambda p: {
        "synced_orders": 3,
        "tracking_updates": 3,
        "provider": f"{p.get('provider', 'pathao')} (mock)",
    },
    "payment_sync": lambda p: {
        "checked_payments": 5,
        "updated": 2,
        "provider": f"{p.get('provider', 'sslcommerz')} (mock)",
    },
    "marketplace_product_sync": lambda p: {
        "exported": 10,
        "failed": 0,
        "provider": f"{p.get('provider', 'facebook')} (mock)",
    },
    "marketplace_order_sync": lambda p: {
        "imported": 2,
        "skipped": 0,
        "provider": f"{p.get('provider', 'daraz')} (mock)",
    },
}


def _run_mock(job: BackgroundJob) -> None:
    now = datetime.now(tz=timezone.utc)
    job.started_at = now
    job.status = "running"

    handler = _MOCK_HANDLERS.get(job.job_type)
    if handler:
        job.result = handler(job.payload or {})  # type: ignore[operator]
    else:
        job.result = {"message": "completed (mock)"}

    job.status = "done"
    job.completed_at = datetime.now(tz=timezone.utc)


def _job_dict(j: BackgroundJob) -> dict:
    return {
        "id": j.id,
        "job_type": j.job_type,
        "status": j.status,
        "payload": j.payload,
        "result": j.result,
        "error": j.error,
        "retry_count": j.retry_count,
        "scheduled_at": j.scheduled_at.isoformat() if j.scheduled_at else None,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "created_at": j.created_at.isoformat() if j.created_at else None,
    }


@router.post("/enqueue")
async def enqueue_job(body: dict, merchant: CurrentMerchant, db: DB) -> dict:
    job = BackgroundJob(
        merchant_id=merchant.id,
        job_type=body.get("job_type", "unknown"),
        status="queued",
        payload=body.get("payload", {}),
    )
    db.add(job)
    await db.flush()
    _run_mock(job)
    await db.commit()
    await db.refresh(job)
    return {"success": True, "data": _job_dict(job)}


@router.get("")
async def list_jobs(
    merchant: CurrentMerchant,
    db: DB,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    q = (
        select(BackgroundJob)
        .where(BackgroundJob.merchant_id == merchant.id)
        .order_by(desc(BackgroundJob.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    jobs = result.scalars().all()

    total_r = await db.execute(
        select(func.count())
        .select_from(BackgroundJob)
        .where(BackgroundJob.merchant_id == merchant.id)
    )
    total = total_r.scalar() or 0

    return {"success": True, "data": {"items": [_job_dict(j) for j in jobs], "total": total}}


@router.get("/{job_id}")
async def get_job(job_id: str, merchant: CurrentMerchant, db: DB) -> dict:
    result = await db.execute(
        select(BackgroundJob).where(
            BackgroundJob.id == job_id,
            BackgroundJob.merchant_id == merchant.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job not found")
    return {"success": True, "data": _job_dict(job)}


@router.post("/{job_id}/retry")
async def retry_job(job_id: str, merchant: CurrentMerchant, db: DB) -> dict:
    result = await db.execute(
        select(BackgroundJob).where(
            BackgroundJob.id == job_id,
            BackgroundJob.merchant_id == merchant.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job not found")

    job.retry_count += 1
    job.error = None
    _run_mock(job)
    await db.commit()
    await db.refresh(job)
    return {"success": True, "data": _job_dict(job)}
