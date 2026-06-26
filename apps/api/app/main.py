import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)s}',
    datefmt="%Y-%m-%dT%H:%M:%S",
)

from app.core.config import get_settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    UnprocessableException,
    bad_request_handler,
    conflict_handler,
    forbidden_handler,
    not_found_handler,
    rate_limit_handler,
    unauthorized_handler,
    unprocessable_handler,
)
from app.db.redis import close_redis, init_redis
from app.routers import (
    agents,
    ai_provider,
    analytics,
    audit_logs,
    backup,
    integrations,
    assistant,
    auth,
    campaigns,
    commerce,
    customers,
    health as health_router,
    hermit,
    inventory,
    jobs,
    media,
    merchant,
    notifications,
    orders,
    products,
    public,
    reports,
    reviews,
    seller_tools,
    strategic,
    system as system_router,
    webhooks,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="SellerMate AI",
    description="Merchant OS for Bangladeshi f-commerce sellers",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_access_log = logging.getLogger("sellermate.access")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    _access_log.info(
        '"method":"%s","path":"%s","status":%d,"ms":%.1f',
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    from app.routers.system import record_request
    record_request(request.method, request.url.path, response.status_code)
    return response

app.add_exception_handler(NotFoundException, not_found_handler)
app.add_exception_handler(ConflictException, conflict_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_handler)
app.add_exception_handler(ForbiddenException, forbidden_handler)
app.add_exception_handler(BadRequestException, bad_request_handler)
app.add_exception_handler(UnprocessableException, unprocessable_handler)
app.add_exception_handler(RateLimitException, rate_limit_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        },
    )


API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
app.include_router(merchant.router, prefix=f"{API_PREFIX}/merchant", tags=["merchant"])
app.include_router(products.router, prefix=f"{API_PREFIX}/products", tags=["products"])
app.include_router(inventory.router, prefix=f"{API_PREFIX}/inventory", tags=["inventory"])
app.include_router(orders.router, prefix=f"{API_PREFIX}/orders", tags=["orders"])
app.include_router(customers.router, prefix=f"{API_PREFIX}/customers", tags=["customers"])
app.include_router(analytics.router, prefix=f"{API_PREFIX}/analytics", tags=["analytics"])
app.include_router(assistant.router, prefix=f"{API_PREFIX}/assistant", tags=["assistant"])
app.include_router(hermit.router, prefix=f"{API_PREFIX}/ai", tags=["hermit"])
app.include_router(ai_provider.router, prefix=f"{API_PREFIX}/ai", tags=["ai_provider"])
app.include_router(strategic.router, prefix=f"{API_PREFIX}/ai/strategic", tags=["strategic"])
app.include_router(reviews.router, prefix=f"{API_PREFIX}/reviews", tags=["reviews"])
app.include_router(seller_tools.router, prefix=f"{API_PREFIX}/ai/seller-tools", tags=["seller_tools"])
app.include_router(commerce.router, prefix=f"{API_PREFIX}/commerce", tags=["commerce"])
app.include_router(campaigns.router, prefix=f"{API_PREFIX}/campaigns", tags=["campaigns"])
app.include_router(reports.router, prefix=f"{API_PREFIX}/reports", tags=["reports"])
app.include_router(notifications.router, prefix=f"{API_PREFIX}/notifications", tags=["notifications"])
app.include_router(integrations.router, prefix=f"{API_PREFIX}/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix=f"{API_PREFIX}/webhooks", tags=["webhooks"])
app.include_router(jobs.router, prefix=f"{API_PREFIX}/jobs", tags=["jobs"])
app.include_router(system_router.router, prefix=f"{API_PREFIX}/system", tags=["system"])
app.include_router(health_router.router, prefix=f"{API_PREFIX}/health", tags=["health"])
app.include_router(audit_logs.router, prefix=f"{API_PREFIX}/audit-logs", tags=["audit"])
app.include_router(backup.router, prefix=f"{API_PREFIX}/backup", tags=["backup"])
app.include_router(public.router, prefix=f"{API_PREFIX}/public", tags=["public"])
app.include_router(media.router, prefix=f"{API_PREFIX}/media", tags=["media"])
app.include_router(agents.router, prefix=f"{API_PREFIX}/agents", tags=["agents"])


@app.get("/health", tags=["health"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "version": app.version}
