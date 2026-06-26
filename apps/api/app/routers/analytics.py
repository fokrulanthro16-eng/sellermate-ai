from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentMerchant, DB
from app.schemas.analytics import (
    CustomerMetricsOut,
    DashboardMetrics,
    InventoryHealthOut,
    OrderBreakdownOut,
    OverviewMetrics,
    RevenueSeriesOut,
    TopProductItem,
)
from app.schemas.common import SuccessResponse
from app.services import analytics_service

router = APIRouter(tags=["analytics"])


@router.get("/dashboard", response_model=SuccessResponse[DashboardMetrics])
async def dashboard(merchant: CurrentMerchant, db: DB):
    metrics = await analytics_service.get_dashboard(db, merchant.id)
    return SuccessResponse(data=metrics)


@router.get("/customers", response_model=SuccessResponse[CustomerMetricsOut])
async def customer_metrics(
    merchant: CurrentMerchant,
    db: DB,
    from_date: str = Query(..., description="YYYY-MM-DD"),
    to_date: str = Query(..., description="YYYY-MM-DD"),
):
    from_dt, to_dt = _parse_dates(from_date, to_date)
    metrics = await analytics_service.get_customer_metrics(db, merchant.id, from_dt, to_dt)
    return SuccessResponse(data=metrics)


def _parse_dates(from_date: str, to_date: str) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(from_date)
    end = datetime.fromisoformat(to_date) + timedelta(days=1) - timedelta(seconds=1)
    return start, end


@router.get("/overview", response_model=SuccessResponse[OverviewMetrics])
async def overview(
    merchant: CurrentMerchant,
    db: DB,
    from_date: str = Query(..., description="YYYY-MM-DD"),
    to_date: str = Query(..., description="YYYY-MM-DD"),
):
    from_dt, to_dt = _parse_dates(from_date, to_date)
    metrics = await analytics_service.get_overview(db, merchant.id, from_dt, to_dt)
    return SuccessResponse(data=metrics)


@router.get("/revenue", response_model=SuccessResponse[RevenueSeriesOut])
async def revenue_series(
    merchant: CurrentMerchant,
    db: DB,
    from_date: str = Query(...),
    to_date: str = Query(...),
    period: str = Query("day", pattern="^(day|week|month)$"),
):
    from_dt, to_dt = _parse_dates(from_date, to_date)
    series = await analytics_service.get_revenue_series(db, merchant.id, period, from_dt, to_dt)
    return SuccessResponse(data=series)


@router.get("/orders", response_model=SuccessResponse[OrderBreakdownOut])
async def order_breakdown(
    merchant: CurrentMerchant,
    db: DB,
    from_date: str = Query(...),
    to_date: str = Query(...),
):
    from_dt, to_dt = _parse_dates(from_date, to_date)
    breakdown = await analytics_service.get_order_breakdown(db, merchant.id, from_dt, to_dt)
    return SuccessResponse(data=breakdown)


@router.get("/products/top", response_model=SuccessResponse[list[TopProductItem]])
async def top_products(
    merchant: CurrentMerchant,
    db: DB,
    from_date: str = Query(...),
    to_date: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    from_dt, to_dt = _parse_dates(from_date, to_date)
    items = await analytics_service.get_top_products(db, merchant.id, from_dt, to_dt, limit)
    return SuccessResponse(data=items)


@router.get("/inventory", response_model=SuccessResponse[InventoryHealthOut])
async def inventory_health(merchant: CurrentMerchant, db: DB):
    health = await analytics_service.get_inventory_health(db, merchant.id)
    return SuccessResponse(data=health)
