"""
AI Assistant routing — three-level priority:

  1. Gemini 2.5 Flash  (GEMINI_API_KEY set)     — real LLM with tool calling
  2. Anthropic Claude  (ANTHROPIC_API_KEY set)   — real LLM via LangChain
  3. Package Engine    (no key required)         — rapidfuzz intent + numpy trend + real DB
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.merchant import Merchant

settings = get_settings()


async def run_agent(
    merchant: Merchant,
    history: list,
    user_message: str,
    db: AsyncSession,
    today_stats: dict | None = None,
) -> AsyncGenerator[str, None]:

    # ── Priority 1: Gemini 2.5 Flash ──────────────────────────
    if settings.gemini_api_key and settings.gemini_api_key.strip():
        from app.ai.gemini_agent import run_gemini_agent
        async for chunk in run_gemini_agent(merchant, history, user_message, db, today_stats):
            yield chunk
        return

    # ── Priority 2: Anthropic Claude (LangChain) ──────────────
    if settings.anthropic_api_key and settings.anthropic_api_key.strip():
        from app.ai.tools.analytics_tools import make_analytics_tools
        from app.ai.tools.customer_tools import make_customer_tools
        from app.ai.tools.inventory_tools import make_inventory_tools
        from app.ai.tools.order_tools import make_order_tools
        from app.ai.tools.product_tools import make_product_tools
        from app.ai.prompts.system import build_system_prompt
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

        tools = [
            *make_inventory_tools(db, str(merchant.id)),
            *make_order_tools(db, str(merchant.id)),
            *make_customer_tools(db, str(merchant.id)),
            *make_product_tools(db, str(merchant.id)),
            *make_analytics_tools(db, str(merchant.id)),
        ]
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=settings.anthropic_api_key,
            max_tokens=1024,
            streaming=True,
        ).bind_tools(tools)

        system_prompt = build_system_prompt(merchant, today_stats or {})
        messages = [SystemMessage(content=system_prompt)] + history + [HumanMessage(content=user_message)]
        tool_map = {t.name: t for t in tools}
        full_response = ""

        while True:
            tool_calls: list = []
            async for chunk in llm.astream(messages):
                if chunk.content:
                    text = chunk.content if isinstance(chunk.content, str) else ""
                    if text:
                        full_response += text
                        yield text
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)

            if not tool_calls:
                break

            ai_msg = AIMessage(content=full_response, tool_calls=tool_calls)
            messages.append(ai_msg)
            for tc in tool_calls:
                tool_fn = tool_map.get(tc["name"])
                try:
                    tool_result = await tool_fn.ainvoke(tc["args"]) if tool_fn else "Tool not found."
                except Exception as e:
                    tool_result = f"Error: {e}"
                messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
            full_response = ""
        return

    # ── Priority 3: Package Engine (no API key required) ──────
    from app.ai.package_engine import stream_package_engine
    # Convert LangChain BaseMessage history → plain dicts for the package engine
    simple_history = [
        {
            "role": "user" if getattr(m, "type", "") == "human" else "assistant",
            "content": str(getattr(m, "content", "")),
        }
        for m in history
        if getattr(m, "content", "")
    ]
    async for chunk in stream_package_engine(merchant, user_message, db, history=simple_history):
        yield chunk
