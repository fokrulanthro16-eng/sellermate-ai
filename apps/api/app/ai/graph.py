"""
LangGraph StateGraph definition for the SellerMate AI agent.
The agent runs as a simple ReAct loop: LLM → tools → LLM → … → end.
This module is kept for future graph-level features (memory, multi-step planning).
For streaming, use agent.run_agent() directly instead.
"""
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.ai.state import AgentState
from app.core.config import get_settings

settings = get_settings()


def build_graph(tools: list):
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=settings.anthropic_api_key,
        max_tokens=1024,
    ).bind_tools(tools)

    def call_llm(state: AgentState) -> dict:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")

    return graph.compile()
