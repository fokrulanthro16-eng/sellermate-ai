"""
Gemini 2.5 Flash AI Agent with real tool calling.
Uses google-genai SDK (current, replaces deprecated google-generativeai).
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

from google import genai
from google.genai import types
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductVariant
from app.models.strategic_insight import StrategicInsight

settings = get_settings()

# ── Tool Declarations ─────────────────────────────────────────────────────────

_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_low_stock_items",
            description=(
                "Get all products and variants that are low on stock or completely out of stock. "
                "Use when the user asks about inventory alerts, low stock, or stock shortages."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Max items to return. Default 15.",
                    )
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_inventory_status",
            description=(
                "Check current stock levels for a specific product by name. "
                "Returns all variants with quantities and stock status."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(
                        type=types.Type.STRING,
                        description="Product name to check (partial match works)",
                    )
                },
                required=["product_name"],
            ),
        ),
        types.FunctionDeclaration(
            name="search_products",
            description=(
                "Search and list products by name, Bangla name, SKU, or category. "
                "Returns product details with stock and price."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search term — product name, Bangla name, or SKU",
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Optional category filter (e.g. পোশাক, ইলেকট্রনিক্স)",
                    ),
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_top_products",
            description=(
                "Get best-selling products ranked by quantity sold in delivered orders. "
                "Use for 'which product sells most', 'top products', 'best sellers' questions."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Number of products to return. Default 5.",
                    ),
                    "period_days": types.Schema(
                        type=types.Type.INTEGER,
                        description="Days of history to analyse. Default 30.",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_order_summary",
            description=(
                "Get order statistics and revenue for a time period. "
                "Includes counts, revenue, status breakdown, and cancellation rate."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "period": types.Schema(
                        type=types.Type.STRING,
                        description="'today', 'week' (7 days), or 'month' (30 days). Default 'week'.",
                    )
                },
            ),
        ),
        types.FunctionDeclaration(
            name="search_orders",
            description=(
                "Search orders by order number, customer name, or phone. "
                "Optionally filter by status. Returns recent matches."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Order number, customer name, or phone",
                    ),
                    "status": types.Schema(
                        type=types.Type.STRING,
                        description="PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, RETURNED",
                    ),
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Max results. Default 10.",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_customer_info",
            description=(
                "Find customers by name or phone number. "
                "Returns purchase history, total spent, and tags."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Customer name or phone number",
                    )
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_top_customers",
            description=(
                "Get top customers ranked by total spending. "
                "Use for 'VIP customers', 'best customers', 'most valuable customers'."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Number of top customers to return. Default 5.",
                    )
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_revenue_analytics",
            description=(
                "Get detailed revenue analytics: total revenue, cash collected, "
                "average order value, and collection rate for a period."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "period": types.Schema(
                        type=types.Type.STRING,
                        description="'today', 'week' (7 days), or 'month' (30 days). Default 'month'.",
                    )
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_strategic_insights",
            description=(
                "Get AI strategic analysis: trust score and fraud risk assessment. "
                "Use for 'trust score', 'fraud risk', 'business health', 'AI analysis' questions."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
    ]
)


# ── Tool Implementations (Async DB Queries) ───────────────────────────────────

def _make_tools(db: AsyncSession, merchant_id: str) -> dict:
    """Return tool_name → async callable, all bound to db + merchant_id."""

    async def get_low_stock_items(limit: int = 15) -> str:
        result = await db.execute(
            select(
                Product.name,
                ProductVariant.name.label("vname"),
                ProductVariant.stock_quantity,
                ProductVariant.low_stock_alert,
            )
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .where(
                Product.merchant_id == merchant_id,
                ProductVariant.stock_quantity <= ProductVariant.low_stock_alert,
            )
            .order_by(ProductVariant.stock_quantity.asc())
            .limit(limit)
        )
        rows = result.all()
        if not rows:
            return "All products are adequately stocked. No low-stock or out-of-stock items."
        lines = []
        for r in rows:
            display = r.name if not r.vname or r.vname == r.name else f"{r.name} — {r.vname}"
            if r.stock_quantity == 0:
                status = "OUT OF STOCK ❌"
            else:
                status = f"{r.stock_quantity} remaining ⚠️ (threshold: {r.low_stock_alert})"
            lines.append(f"• {display}: {status}")
        return "\n".join(lines)

    async def get_inventory_status(product_name: str) -> str:
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.variants))
            .where(
                Product.merchant_id == merchant_id,
                or_(
                    Product.name.ilike(f"%{product_name}%"),
                    Product.name_bangla.ilike(f"%{product_name}%"),
                ),
            )
            .limit(5)
        )
        products = result.scalars().all()
        if not products:
            return f'No product found matching "{product_name}".'
        lines = []
        for p in products:
            total = sum(v.stock_quantity for v in p.variants)
            lines.append(f"Product: {p.name} (total stock: {total})")
            for v in p.variants:
                if v.stock_quantity == 0:
                    flag = "OUT OF STOCK"
                elif v.stock_quantity <= v.low_stock_alert:
                    flag = "LOW STOCK"
                else:
                    flag = "OK"
                lines.append(f"  • {v.name}: {v.stock_quantity} units [{flag}] | ৳{v.price:,.0f}")
        return "\n".join(lines)

    async def search_products(query: str, category: str = "") -> str:
        stmt = (
            select(Product)
            .options(selectinload(Product.variants))
            .where(
                Product.merchant_id == merchant_id,
                Product.is_active.is_(True),
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.name_bangla.ilike(f"%{query}%"),
                    Product.sku.ilike(f"%{query}%"),
                ),
            )
        )
        if category:
            stmt = stmt.where(Product.category.ilike(f"%{category}%"))
        result = await db.execute(stmt.limit(10))
        products = result.scalars().all()
        if not products:
            return f'No products found for "{query}".'
        lines = []
        for p in products:
            total_stock = sum(v.stock_quantity for v in p.variants)
            price = f"৳{p.base_price:,.0f}" if p.base_price else "varies"
            lines.append(
                f"• {p.name} ({p.name_bangla or '—'}) | Category: {p.category or 'N/A'} | "
                f"Price: {price} | {len(p.variants)} variant(s) | Stock: {total_stock}"
            )
        return "\n".join(lines)

    async def get_top_products(limit: int = 5, period_days: int = 30) -> str:
        since = datetime.now(timezone.utc) - timedelta(days=period_days)
        result = await db.execute(
            select(
                Product.name,
                func.sum(OrderItem.quantity).label("sold"),
                func.sum(OrderItem.total_price).label("revenue"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Product.merchant_id == merchant_id,
                Order.status == OrderStatus.DELIVERED,
                Order.created_at >= since,
            )
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )
        rows = result.all()
        if not rows:
            return f"No delivered orders in the last {period_days} days."
        lines = [f"Top {len(rows)} products — last {period_days} days (by units sold):"]
        for i, r in enumerate(rows, 1):
            lines.append(
                f"{i}. {r.name} — {int(r.sold)} units sold | Revenue: ৳{float(r.revenue):,.0f}"
            )
        return "\n".join(lines)

    async def get_order_summary(period: str = "week") -> str:
        now = datetime.now(timezone.utc)
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "Today"
        elif period == "month":
            start = now - timedelta(days=30)
            label = "Last 30 days"
        else:
            start = now - timedelta(days=7)
            label = "Last 7 days"

        agg = await db.execute(
            select(
                func.count(Order.id).label("total"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
                func.coalesce(func.sum(Order.due_amount), 0).label("due"),
            ).where(Order.merchant_id == merchant_id, Order.created_at >= start)
        )
        row = agg.one()
        total = int(row.total)
        revenue = float(row.revenue)
        due = float(row.due)
        aov = revenue / total if total > 0 else 0

        breakdown: dict[str, int] = {}
        for s in OrderStatus:
            cnt = await db.execute(
                select(func.count(Order.id)).where(
                    Order.merchant_id == merchant_id,
                    Order.status == s,
                    Order.created_at >= start,
                )
            )
            n = int(cnt.scalar() or 0)
            if n > 0:
                breakdown[s.value] = n

        lines = [
            f"Order Summary — {label}:",
            f"• Total orders: {total}",
            f"• Revenue: ৳{revenue:,.0f}",
            f"• Avg order value: ৳{aov:,.0f}",
            f"• Outstanding dues: ৳{due:,.0f}",
            "• By status:",
        ]
        for status, count in breakdown.items():
            lines.append(f"  – {status}: {count}")

        if total > 0:
            cancel_rate = breakdown.get("CANCELLED", 0) / total * 100
            if cancel_rate > 20:
                lines.append(f"⚠️ High cancellation rate: {cancel_rate:.1f}% — investigate causes")

        return "\n".join(lines)

    async def search_orders(query: str = "", status: str = "", limit: int = 10) -> str:
        stmt = (
            select(Order)
            .options(selectinload(Order.customer))
            .where(Order.merchant_id == merchant_id)
        )
        if status:
            try:
                stmt = stmt.where(Order.status == OrderStatus(status.upper()))
            except ValueError:
                pass
        if query:
            stmt = stmt.join(Customer, Order.customer_id == Customer.id, isouter=True).where(
                or_(
                    Order.order_number.ilike(f"%{query}%"),
                    Customer.name.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%"),
                )
            )
        stmt = stmt.order_by(Order.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        orders = result.scalars().all()
        if not orders:
            return "No orders found matching the criteria."
        lines = []
        for o in orders:
            cname = o.customer.name if o.customer else "Unknown"
            date_str = o.created_at.strftime("%d/%m/%Y") if o.created_at else "—"
            lines.append(
                f"• {o.order_number} | {cname} | ৳{o.total_amount:,.0f} | "
                f"{o.status.value} | {o.payment_status.value} | {date_str}"
            )
        return "\n".join(lines)

    async def get_customer_info(query: str) -> str:
        result = await db.execute(
            select(Customer)
            .where(
                Customer.merchant_id == merchant_id,
                or_(
                    Customer.name.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%"),
                ),
            )
            .order_by(Customer.total_spent.desc())
            .limit(10)
        )
        customers = result.scalars().all()
        if not customers:
            return f'No customers found matching "{query}".'
        lines = []
        for c in customers:
            tags = ", ".join(c.tags) if c.tags else "none"
            retention = "Repeat customer" if c.total_orders >= 2 else "New customer"
            lines.append(
                f"• {c.name} | {c.phone} | Orders: {c.total_orders} | "
                f"Spent: ৳{c.total_spent:,.0f} | {retention} | Tags: {tags}"
            )
        return "\n".join(lines)

    async def get_top_customers(limit: int = 5) -> str:
        result = await db.execute(
            select(Customer)
            .where(Customer.merchant_id == merchant_id)
            .order_by(Customer.total_spent.desc())
            .limit(limit)
        )
        customers = result.scalars().all()
        if not customers:
            return "No customers found."
        total_r = await db.execute(
            select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
        )
        total = int(total_r.scalar() or 0)
        lines = [f"Top {len(customers)} customers by spending (out of {total} total):"]
        for i, c in enumerate(customers, 1):
            tags = ", ".join(c.tags) if c.tags else "—"
            lines.append(
                f"{i}. {c.name} ({c.phone}) | ৳{c.total_spent:,.0f} total | "
                f"{c.total_orders} orders | Tags: {tags}"
            )
        return "\n".join(lines)

    async def get_revenue_analytics(period: str = "month") -> str:
        now = datetime.now(timezone.utc)
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "Today"
        elif period == "week":
            start = now - timedelta(days=7)
            label = "Last 7 days"
        else:
            start = now - timedelta(days=30)
            label = "Last 30 days"

        total_r = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.status != OrderStatus.CANCELLED,
                Order.created_at >= start,
            )
        )
        paid_r = await db.execute(
            select(func.coalesce(func.sum(Order.paid_amount), 0)).where(
                Order.merchant_id == merchant_id,
                Order.status != OrderStatus.CANCELLED,
                Order.created_at >= start,
            )
        )
        count_r = await db.execute(
            select(func.count(Order.id)).where(
                Order.merchant_id == merchant_id,
                Order.created_at >= start,
            )
        )
        total_revenue = float(total_r.scalar() or 0)
        paid = float(paid_r.scalar() or 0)
        order_count = int(count_r.scalar() or 0)
        aov = total_revenue / order_count if order_count > 0 else 0
        collection = paid / total_revenue * 100 if total_revenue > 0 else 0

        return (
            f"Revenue Analytics — {label}:\n"
            f"• Total revenue: ৳{total_revenue:,.0f}\n"
            f"• Orders processed: {order_count}\n"
            f"• Average order value: ৳{aov:,.0f}\n"
            f"• Cash collected: ৳{paid:,.0f}\n"
            f"• Collection rate: {collection:.1f}%\n"
            f"• Outstanding: ৳{total_revenue - paid:,.0f}"
        )

    async def get_strategic_insights() -> str:
        trust_r = await db.execute(
            select(StrategicInsight)
            .where(
                StrategicInsight.merchant_id == merchant_id,
                StrategicInsight.agent_name == "trust_graph",
            )
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        trust = trust_r.scalar_one_or_none()

        fraud_r = await db.execute(
            select(StrategicInsight)
            .where(
                StrategicInsight.merchant_id == merchant_id,
                StrategicInsight.agent_name == "fraud_sentinel",
            )
            .order_by(StrategicInsight.created_at.desc())
            .limit(1)
        )
        fraud = fraud_r.scalar_one_or_none()

        parts = []
        if trust:
            p = trust.payload or {}
            signals = ", ".join(p.get("positive_signals") or []) or "none"
            flags = ", ".join(p.get("risk_flags") or []) or "none"
            parts.append(
                f"TRUST GRAPH:\n"
                f"• Score: {trust.score}/100\n"
                f"• Positive signals: {signals}\n"
                f"• Risk flags: {flags}\n"
                f"• Summary: {p.get('explanation_en', 'N/A')}"
            )
        else:
            parts.append("Trust Score: Not available — visit AI Center and click 'Run Agents'")

        if fraud:
            p = fraud.payload or {}
            patterns = ", ".join(p.get("suspicious_patterns") or []) or "none"
            alerts = ", ".join(p.get("alert_reasons") or []) or "none"
            parts.append(
                f"\nFRAUD SENTINEL:\n"
                f"• Risk Score: {fraud.score}/100\n"
                f"• Risk Level: {p.get('risk_level', 'N/A')}\n"
                f"• Suspicious patterns: {patterns}\n"
                f"• Alert reasons: {alerts}\n"
                f"• Summary: {p.get('explanation_en', 'N/A')}"
            )
        else:
            parts.append("\nFraud Report: Not available — visit AI Center and click 'Run Agents'")

        return "\n".join(parts)

    return {
        "get_low_stock_items": get_low_stock_items,
        "get_inventory_status": get_inventory_status,
        "search_products": search_products,
        "get_top_products": get_top_products,
        "get_order_summary": get_order_summary,
        "search_orders": search_orders,
        "get_customer_info": get_customer_info,
        "get_top_customers": get_top_customers,
        "get_revenue_analytics": get_revenue_analytics,
        "get_strategic_insights": get_strategic_insights,
    }


# ── System Prompt ─────────────────────────────────────────────────────────────

def _build_system_prompt(merchant: Merchant, today_stats: dict) -> str:
    return f"""You are SellerMate AI — the dedicated business intelligence assistant for {merchant.business_name}.

You serve Bangladeshi e-commerce merchants with real-time data insights from their store database.

## LANGUAGE RULE (CRITICAL — follow exactly)
- If the user writes in Bangla/Bengali script → respond ENTIRELY in Bangla
- If the user writes in English → respond ENTIRELY in English
- NEVER mix languages in a single response
- This applies to all labels, headings, and list items too

## Business Context
- Business: {merchant.business_name}
- Owner: {merchant.owner_name}
- Type: {merchant.business_type.value}
- Today's revenue so far: ৳{today_stats.get('revenue', 0):,.0f}
- Today's orders: {today_stats.get('orders', 0)}
- Pending orders: {today_stats.get('pending', 0)}

## Tool Usage Rules
ALWAYS call the appropriate tool to fetch real data before answering any factual question.
Never estimate or guess numbers — fetch them from the database.

Tool selection guide:
- "low stock", "stock alerts", "কম স্টক", "ইনভেন্টরি সমস্যা" → get_low_stock_items
- Specific product stock check → get_inventory_status
- Find/list products, "পণ্য খুঁজি" → search_products
- "best seller", "top product", "সবচেয়ে বেশি বিক্রি", "কোন পণ্য জনপ্রিয়" → get_top_products
- Order counts, revenue summary → get_order_summary
- Find specific order/customer order → search_orders
- Find customer by name/phone → get_customer_info
- "VIP", "top customer", "সেরা গ্রাহক", "বেশি কেনা" → get_top_customers
- Revenue analysis, collection rate → get_revenue_analytics
- Trust/fraud/AI score, "ট্রাস্ট স্কোর", "ফ্রড রিস্ক" → get_strategic_insights

## Response Format
- Use ৳ for all currency (e.g., ৳1,23,456)
- Use markdown formatting (bold, lists, headers) for clarity
- Be concise and actionable — interpret the data, don't just list numbers
- Add a brief insight or recommendation when the data suggests one
"""


# ── History Conversion ────────────────────────────────────────────────────────

def _to_gemini_contents(lc_history: list) -> list[types.Content]:
    """Convert LangChain message history to Gemini Content objects."""
    from langchain_core.messages import AIMessage, HumanMessage

    contents = []
    for msg in lc_history:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        if not text.strip():
            continue
        if isinstance(msg, HumanMessage):
            contents.append(types.Content(role="user", parts=[types.Part(text=text)]))
        elif isinstance(msg, AIMessage):
            contents.append(types.Content(role="model", parts=[types.Part(text=text)]))
    return contents


# ── Main Agent ────────────────────────────────────────────────────────────────

async def run_gemini_agent(
    merchant: Merchant,
    history: list,
    user_message: str,
    db: AsyncSession,
    today_stats: dict | None = None,
) -> AsyncGenerator[str, None]:
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
    except Exception as e:
        yield f"⚠️ Gemini configuration error: {e}"
        return

    system_prompt = _build_system_prompt(merchant, today_stats or {})
    tool_map = _make_tools(db, str(merchant.id))
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[_TOOL],
        temperature=0.7,
        max_output_tokens=2048,
    )

    # Build initial contents from history + current message
    contents: list[types.Content] = _to_gemini_contents(history)
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    max_rounds = 6
    for _ in range(max_rounds):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
        except Exception as e:
            yield f"⚠️ AI generation error: {e}"
            return

        if not response.candidates:
            yield "⚠️ No response from Gemini. Request may have been blocked. Please rephrase."
            return

        candidate_content = response.candidates[0].content

        # Collect function calls from this response
        fn_calls = [
            p for p in candidate_content.parts
            if p.function_call and p.function_call.name
        ]

        if not fn_calls:
            # No more tool calls — stream the final text response
            final_text = "".join(
                p.text for p in candidate_content.parts
                if hasattr(p, "text") and p.text
            )
            if not final_text.strip():
                is_bn = any(ord(c) > 0x0980 for c in user_message)
                final_text = (
                    "আমি দুঃখিত, উত্তর তৈরি করতে পারিনি। আবার চেষ্টা করুন।"
                    if is_bn
                    else "I couldn't generate a response. Please try rephrasing your question."
                )
            # Pseudo-stream in chunks for live feel
            chunk_size = 50
            for i in range(0, len(final_text), chunk_size):
                yield final_text[i : i + chunk_size]
                await asyncio.sleep(0.012)
            return

        # Append model's function-call content to history
        contents.append(candidate_content)

        # Execute all function calls and batch their responses
        tool_parts: list[types.Part] = []
        for fc_part in fn_calls:
            fn_name = fc_part.function_call.name
            fn_args = dict(fc_part.function_call.args) if fc_part.function_call.args else {}
            tool_fn = tool_map.get(fn_name)
            try:
                result = await tool_fn(**fn_args) if tool_fn else f"Unknown tool: {fn_name}"
            except Exception as e:
                result = f"Tool error ({fn_name}): {e}"

            tool_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": str(result)},
                    )
                )
            )

        contents.append(types.Content(role="user", parts=tool_parts))

    # Exceeded max rounds
    is_bn = any(ord(c) > 0x0980 for c in user_message)
    yield (
        "⚠️ প্রশ্নটি আরো নির্দিষ্টভাবে করুন — অনেক ধাপ লেগেছে।"
        if is_bn
        else "⚠️ Response took too many steps. Please ask a more specific question."
    )
