"""Pydantic schemas for all Phase 4 Commerce Automation endpoints."""
from __future__ import annotations

from pydantic import BaseModel


# ── Price Recommendations ──────────────────────────────────────────────────────

class PriceRecommendationOut(BaseModel):
    product_id: str
    product_name: str
    current_price: float
    recommended_price: float
    change_pct: float
    action: str
    reason_en: str
    reason_bn: str
    confidence: str


# ── Demand Predictions ─────────────────────────────────────────────────────────

class DemandPredictionOut(BaseModel):
    product_id: str
    product_name: str
    units_sold_30d: int
    daily_velocity: float
    predicted_next_30d: int
    trend: str
    confidence: str


# ── Inventory Forecast ─────────────────────────────────────────────────────────

class InventoryForecastOut(BaseModel):
    variant_id: str
    product_id: str
    product_name: str
    variant_name: str
    current_stock: int
    daily_velocity: float
    days_remaining: float
    weeks_remaining: float
    status: str


# ── Restock ───────────────────────────────────────────────────────────────────

class RestockItemOut(BaseModel):
    variant_id: str
    product_id: str
    product_name: str
    variant_name: str
    current_stock: int
    recommended_qty: int
    priority: str
    days_remaining: float


# ── Bundle Recommendations ────────────────────────────────────────────────────

class BundleRecommendationOut(BaseModel):
    product_a_id: str
    product_a_name: str
    product_b_id: str
    product_b_name: str
    co_purchase_count: int
    suggested_discount_pct: float


# ── Best / Worst Sellers ──────────────────────────────────────────────────────

class SellerItemOut(BaseModel):
    product_id: str
    product_name: str
    total_units: int
    total_revenue: float
    order_count: int
    avg_price: float


# ── Customer LTV ──────────────────────────────────────────────────────────────

class CustomerLTVOut(BaseModel):
    customer_id: str
    customer_name: str
    phone: str
    total_orders: int
    total_spent: float
    avg_order_value: float
    predicted_ltv_12m: float
    segment: str


# ── Churn Risk ────────────────────────────────────────────────────────────────

class ChurnRiskOut(BaseModel):
    customer_id: str
    customer_name: str
    phone: str
    days_inactive: int
    last_order_date: str
    risk_level: str
    total_orders: int


# ── Revenue Forecast ──────────────────────────────────────────────────────────

class RevenueForecastOut(BaseModel):
    current_30d: float
    predicted_next_30d: float
    growth_pct: float
    trend: str
    confidence: str
    daily_points: list[dict]


# ── Business Health Score ─────────────────────────────────────────────────────

class HealthComponentOut(BaseModel):
    name: str
    name_bn: str
    score: int
    max_score: int
    status: str


class BusinessHealthScoreOut(BaseModel):
    score: int
    grade: str
    components: list[HealthComponentOut]
    strengths: list[str]
    weaknesses: list[str]
    explanation_en: str
    explanation_bn: str


# ── Profit Report ─────────────────────────────────────────────────────────────

class ProfitReportOut(BaseModel):
    period_days: int
    total_revenue: float
    estimated_cogs: float
    gross_profit: float
    gross_margin_pct: float
    total_discounts: float
    total_shipping_cost: float
    net_profit: float
    net_margin_pct: float
    delivered_order_count: int
    total_order_count: int


# ── Tax Summary ───────────────────────────────────────────────────────────────

class TaxSummaryOut(BaseModel):
    period_days: int
    total_revenue: float
    vat_rate_pct: float
    estimated_vat: float
    gross_profit: float
    estimated_income_tax: float
    total_tax_liability: float
    deductible_shipping: float
    deductible_discounts: float
    net_tax_after_deductions: float


# ── Campaigns ─────────────────────────────────────────────────────────────────

class CampaignGenerateRequest(BaseModel):
    campaign_type: str   # fb_post | fb_ad | email | sms
    product_name: str
    product_price: str
    language: str = "bn"
    tone: str = "friendly"
    extra_context: str = ""


class CampaignOut(BaseModel):
    id: str
    title: str
    campaign_type: str
    content: str
    language: str
    status: str
    provider: str
    created_at: str

    class Config:
        from_attributes = True


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    type: str
    priority: str
    title_en: str
    title_bn: str
    body_en: str
    body_bn: str
    action: str
