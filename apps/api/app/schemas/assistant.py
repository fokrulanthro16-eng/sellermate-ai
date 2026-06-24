from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assistant import MessageRole


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    merchant_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
