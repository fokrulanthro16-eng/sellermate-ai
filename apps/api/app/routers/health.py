"""Health check router — /api/v1/health"""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.dependencies import DB

router = APIRouter(tags=["health"])


@router.get("")
async def health_check(db: DB) -> dict:
    db_ok = False
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "components": {
            "api": {"status": "ok"},
            "database": {"status": "ok" if db_ok else "error", "error": db_error},
        },
    }
