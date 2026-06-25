"""
Commerce Automation router — Smart Price, Demand, Inventory, Restock, Bundle, Best/Worst Sellers.
"""
from fastapi import APIRouter, Query

from app.ai.commerce import CommerceEngine
from app.core.dependencies import CurrentMerchant, DB
from app.schemas.commerce import (
    BundleRecommendationOut,
    DemandPredictionOut,
    InventoryForecastOut,
    PriceRecommendationOut,
    RestockItemOut,
    SellerItemOut,
)
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["commerce"])
_engine = CommerceEngine()


@router.get("/price-recommendations", response_model=SuccessResponse[list[PriceRecommendationOut]])
async def price_recommendations(merchant: CurrentMerchant, db: DB):
    data = await _engine.price_recommendations(db, merchant.id)
    return SuccessResponse(data=[PriceRecommendationOut(**vars(d)) for d in data])


@router.get("/demand-predictions", response_model=SuccessResponse[list[DemandPredictionOut]])
async def demand_predictions(merchant: CurrentMerchant, db: DB):
    data = await _engine.demand_predictions(db, merchant.id)
    return SuccessResponse(data=[DemandPredictionOut(**vars(d)) for d in data])


@router.get("/inventory-forecast", response_model=SuccessResponse[list[InventoryForecastOut]])
async def inventory_forecast(merchant: CurrentMerchant, db: DB):
    data = await _engine.inventory_forecast(db, merchant.id)
    return SuccessResponse(data=[InventoryForecastOut(**vars(d)) for d in data])


@router.get("/restock-recommendations", response_model=SuccessResponse[list[RestockItemOut]])
async def restock_recommendations(merchant: CurrentMerchant, db: DB):
    data = await _engine.restock_recommendations(db, merchant.id)
    return SuccessResponse(data=[RestockItemOut(**vars(d)) for d in data])


@router.get("/bundle-recommendations", response_model=SuccessResponse[list[BundleRecommendationOut]])
async def bundle_recommendations(merchant: CurrentMerchant, db: DB):
    data = await _engine.bundle_recommendations(db, merchant.id)
    return SuccessResponse(data=[BundleRecommendationOut(**vars(d)) for d in data])


@router.get("/best-sellers", response_model=SuccessResponse[list[SellerItemOut]])
async def best_sellers(
    merchant: CurrentMerchant,
    db: DB,
    days: int = Query(30, ge=7, le=365),
):
    data = await _engine.best_sellers(db, merchant.id, days)
    return SuccessResponse(data=[SellerItemOut(**vars(d)) for d in data])


@router.get("/worst-sellers", response_model=SuccessResponse[list[SellerItemOut]])
async def worst_sellers(
    merchant: CurrentMerchant,
    db: DB,
    days: int = Query(30, ge=7, le=365),
):
    data = await _engine.worst_sellers(db, merchant.id, days)
    return SuccessResponse(data=[SellerItemOut(**vars(d)) for d in data])
