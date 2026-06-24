from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentMerchant, DB
from app.schemas.assistant import ChatRequest, ConversationOut, MessageOut
from app.schemas.common import MessageResponse, SuccessResponse
from app.services import assistant_service

router = APIRouter(tags=["assistant"])


@router.get("/conversations", response_model=SuccessResponse[list[ConversationOut]])
async def list_conversations(merchant: CurrentMerchant, db: DB):
    convs = await assistant_service.list_conversations(db, merchant.id)
    return SuccessResponse(data=[ConversationOut.model_validate(c) for c in convs])


@router.post("/conversations", response_model=SuccessResponse[ConversationOut], status_code=201)
async def create_conversation(merchant: CurrentMerchant, db: DB):
    conv = await assistant_service.create_conversation(db, merchant.id)
    return SuccessResponse(data=ConversationOut.model_validate(conv))


@router.delete("/conversations/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(conversation_id: str, merchant: CurrentMerchant, db: DB):
    await assistant_service.delete_conversation(db, merchant.id, conversation_id)
    return MessageResponse(message="Conversation deleted")


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=SuccessResponse[list[MessageOut]],
)
async def get_messages(conversation_id: str, merchant: CurrentMerchant, db: DB):
    messages = await assistant_service.get_messages(db, merchant.id, conversation_id)
    return SuccessResponse(data=[MessageOut.model_validate(m) for m in messages])


@router.post("/conversations/{conversation_id}/chat")
async def chat(conversation_id: str, body: ChatRequest, merchant: CurrentMerchant, db: DB):
    async def event_stream():
        async for chunk in assistant_service.stream_chat(
            db, merchant, conversation_id, body.message
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
