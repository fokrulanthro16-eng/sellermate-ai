"""Health check router — /api/v1/health"""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.dependencies import DB

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("")
async def health_check(db: DB) -> dict:
    # ── Database ───────────────────────────────────────────────────────────────
    db_ok = False
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    # ── Redis / Queue ─────────────────────────────────────────────────────────
    redis_ok = False
    redis_error = None
    try:
        from app.db.redis import get_redis
        r = await get_redis()
        if r is not None:
            await r.ping()
            redis_ok = True
        else:
            redis_error = "Redis not initialized"
    except Exception as e:
        redis_error = str(e)

    # ── Storage (S3 / R2) ─────────────────────────────────────────────────────
    storage_configured = bool(settings.s3_access_key and settings.s3_secret_key and settings.s3_bucket_name)
    storage_mode = "s3" if storage_configured else "local_base64"

    # ── AI Provider ───────────────────────────────────────────────────────────
    ai_providers: list[str] = []
    if settings.gemini_api_key:
        ai_providers.append("gemini")
    if settings.openai_api_key:
        ai_providers.append("openai")
    if settings.anthropic_api_key:
        ai_providers.append("anthropic")
    ai_mode = "live" if ai_providers else "mock_fallback"

    overall = "ok" if db_ok else "degraded"

    return {
        "status": overall,
        "version": "1.0.0",
        "app_mode": settings.app_mode,
        "components": {
            "api":      {"status": "ok"},
            "database": {"status": "ok" if db_ok else "error", "error": db_error},
            "queue":    {"status": "ok" if redis_ok else "degraded", "error": redis_error},
            "storage":  {"status": "ok", "mode": storage_mode},
            "ai":       {"status": "ok", "mode": ai_mode, "providers": ai_providers},
        },
    }
