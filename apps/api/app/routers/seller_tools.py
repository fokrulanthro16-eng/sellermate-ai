from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.ai.seller_tools_agent import SellerToolsAgent
from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import NotFoundException
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.strategic_insight import StrategicInsight
from app.schemas.common import SuccessResponse
from app.services import strategic_service

router = APIRouter(tags=["seller_tools"])


class GenerateRequest(BaseModel):
    tool: str
    lang: str = "bn"
    tone: str = "friendly"
    product_id: str | None = None
    order_id: str | None = None
    extra_context: str | None = None


class GenerateOut(BaseModel):
    text: str
    tool: str
    lang: str
    source: str
    context_used: dict[str, Any] = {}


class ToolProductOut(BaseModel):
    id: str
    name: str
    name_bangla: str | None
    category: str
    base_price: str
    sale_price: str | None


@router.get("/products", response_model=SuccessResponse[list[ToolProductOut]])
async def list_tool_products(merchant: CurrentMerchant, db: DB):
    """Products for the tool selector dropdown."""
    result = await db.execute(
        select(Product)
        .where(Product.merchant_id == merchant.id, Product.is_active.is_(True))
        .order_by(Product.name)
        .limit(100)
    )
    rows = result.scalars().all()
    return SuccessResponse(data=[
        ToolProductOut(
            id=p.id,
            name=p.name,
            name_bangla=p.name_bangla,
            category=p.category,
            base_price=str(p.base_price),
            sale_price=str(p.sale_price) if p.sale_price else None,
        )
        for p in rows
    ])


@router.post("/generate", response_model=SuccessResponse[GenerateOut])
async def generate_content(req: GenerateRequest, merchant: CurrentMerchant, db: DB):
    product_dict: dict | None = None
    if req.product_id:
        result = await db.execute(
            select(Product).where(Product.id == req.product_id, Product.merchant_id == merchant.id)
        )
        p = result.scalar_one_or_none()
        if not p:
            raise NotFoundException("Product not found")
        product_dict = {
            "id": p.id,
            "name": p.name,
            "name_bangla": p.name_bangla,
            "description": p.description,
            "description_bangla": p.description_bangla,
            "category": p.category,
            "base_price": str(p.base_price),
            "sale_price": str(p.sale_price) if p.sale_price else None,
        }

    order_dict: dict | None = None
    customer_dict: dict | None = None
    if req.order_id:
        result = await db.execute(
            select(Order).where(Order.id == req.order_id, Order.merchant_id == merchant.id)
        )
        o = result.scalar_one_or_none()
        if not o:
            raise NotFoundException("Order not found")
        order_dict = {
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "total_amount": str(o.total_amount),
        }
        if o.customer_id:
            cr = await db.execute(select(Customer).where(Customer.id == o.customer_id))
            c = cr.scalar_one_or_none()
            if c:
                customer_dict = {"name": c.name, "phone": c.phone}

    insights_dict: dict | None = None
    if req.tool == "daily_action":
        summary = await strategic_service.get_summary(db, merchant.id)
        insights_dict = {
            "trust_score": summary.trust_score,
            "risk_level": summary.risk_level,
        }
        growth_row = await db.execute(
            select(StrategicInsight)
            .where(
                StrategicInsight.merchant_id == merchant.id,
                StrategicInsight.agent_name == "growth_coach",
            )
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        growth = growth_row.scalar_one_or_none()
        if growth and growth.payload:
            insights_dict["trend_direction"] = growth.payload.get("trend_direction")
            insights_dict["revenue_growth_pct"] = growth.payload.get("revenue_growth_pct")

    agent = SellerToolsAgent()
    content = await agent.generate(
        tool=req.tool,
        lang=req.lang,
        tone=req.tone,
        product=product_dict,
        order=order_dict,
        customer=customer_dict,
        insights=insights_dict,
        extra_context=req.extra_context,
    )

    return SuccessResponse(data=GenerateOut(
        text=content.text,
        tool=req.tool,
        lang=req.lang,
        source=content.source,
        context_used=content.context_used,
    ))
