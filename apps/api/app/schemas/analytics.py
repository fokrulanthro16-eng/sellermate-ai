from pydantic import BaseModel, Field


class RevenuePoint(BaseModel):
    date: str
    revenue: float
    orders: int


class TopProductItem(BaseModel):
    product_id: str
    product_name: str
    total_revenue: float
    total_quantity: int


class TopCustomerItem(BaseModel):
    customer_id: str
    customer_name: str
    total_orders: int
    total_spent: float


class DashboardMetrics(BaseModel):
    today_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    total_orders: int
    delivered_orders: int
    cancelled_orders: int
    repeat_customers: int
    average_order_value: float
    top_products: list[TopProductItem]
    top_customers: list[TopCustomerItem]


class ChannelBreakdown(BaseModel):
    channel: str
    count: int
    revenue: float


class OverviewMetrics(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    average_order_value: float
    revenue_change_pct: float
    orders_change_pct: float
    customers_change_pct: float


class RevenueSeriesOut(BaseModel):
    period: str
    points: list[RevenuePoint]


class OrderBreakdownOut(BaseModel):
    by_status: dict[str, int]
    by_channel: list[ChannelBreakdown]
    by_payment_method: dict[str, int]
    by_payment_status: dict[str, int]


class CustomerMetricsOut(BaseModel):
    new_customers: int
    returning_customers: int
    top_customers: list[dict]


class InventoryHealthOut(BaseModel):
    total_variants: int
    in_stock: int
    low_stock: int
    out_of_stock: int
    low_stock_items: list[dict]


class AnalyticsFilters(BaseModel):
    from_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    to_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    period: str = Field("day", pattern="^(day|week|month)$")
