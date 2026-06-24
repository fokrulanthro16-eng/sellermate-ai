from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated, TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    merchant_id: str
    merchant_name: str
    merchant_business_type: str
