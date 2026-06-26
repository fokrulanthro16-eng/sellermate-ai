"""System information, metrics, and uptime endpoints."""
from __future__ import annotations

import sys
import platform
import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.config import get_settings
from app.core.dependencies import CurrentMerchant, DB

router = APIRouter(tags=["system"])
settings = get_settings()

_START_TIME = time.time()
_req_counts: dict[str, int] = defaultdict(int)
_err_counts: dict[str, int] = defaultdict(int)


def record_request(method: str, path: str, status: int) -> None:
    key = f"{method} {path}"
    _req_counts[key] += 1
    if status >= 400:
        _err_counts[key] += 1


@router.get("/uptime")
async def get_uptime() -> dict:
    uptime_s = int(time.time() - _START_TIME)
    return {
        "status": "ok",
        "uptime_seconds": uptime_s,
        "started_at": datetime.fromtimestamp(_START_TIME, tz=timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/info")
async def system_info(merchant: CurrentMerchant, db: DB) -> dict:
    try:
        r = await db.execute(text("SELECT version_num FROM alembic_version"))
        revision = r.scalar() or "unknown"
    except Exception:
        revision = "error"

    uptime_s = int(time.time() - _START_TIME)

    return {
        "success": True,
        "data": {
            "version": "1.0.0",
            "phase": "11.5",
            "app_mode": settings.app_mode,
            "is_beta": settings.is_beta,
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "uptime_seconds": uptime_s,
            "alembic_revision": revision,
            "is_production": settings.is_production,
            "env_keys": {
                "gemini": bool(settings.gemini_api_key),
                "openai": bool(settings.openai_api_key),
                "anthropic": bool(settings.anthropic_api_key),
                "whatsapp": bool(settings.whatsapp_access_token),
                "s3": bool(settings.s3_access_key),
            },
        },
    }


@router.get("/metrics")
async def get_metrics(merchant: CurrentMerchant) -> dict:
    top_paths = sorted(_req_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "success": True,
        "data": {
            "uptime_seconds": int(time.time() - _START_TIME),
            "total_requests": sum(_req_counts.values()),
            "total_errors": sum(_err_counts.values()),
            "top_paths": [{"path": p, "count": c} for p, c in top_paths],
        },
    }
