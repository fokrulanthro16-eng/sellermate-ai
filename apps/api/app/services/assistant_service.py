from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.assistant import Conversation, Message, MessageRole
from app.models.merchant import Merchant


async def list_conversations(db: AsyncSession, merchant_id: str) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.merchant_id == merchant_id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def create_conversation(db: AsyncSession, merchant_id: str) -> Conversation:
    conv = Conversation(merchant_id=merchant_id)
    db.add(conv)
    await db.flush()
    return conv


async def delete_conversation(
    db: AsyncSession, merchant_id: str, conversation_id: str
) -> None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.merchant_id == merchant_id,
            Conversation.id == conversation_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundException("Conversation not found")
    await db.delete(conv)


async def get_messages(
    db: AsyncSession, merchant_id: str, conversation_id: str
) -> list[Message]:
    result = await db.execute(
        select(Conversation).where(
            Conversation.merchant_id == merchant_id,
            Conversation.id == conversation_id,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Conversation not found")

    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(msgs_result.scalars().all())


async def stream_chat(
    db: AsyncSession,
    merchant: Merchant,
    conversation_id: str,
    user_message: str,
) -> AsyncGenerator[str, None]:
    from app.ai.agent import run_agent
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

    result = await db.execute(
        select(Conversation).where(
            Conversation.merchant_id == merchant.id,
            Conversation.id == conversation_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundException("Conversation not found")

    # Fetch prior history BEFORE saving the new user message so it is not
    # duplicated — agent.py appends user_message as HumanMessage itself.
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(20)
    )
    prior_messages = list(history_result.scalars().all())

    # Convert ORM Message objects → LangChain BaseMessage for the agent.
    lc_history: list[BaseMessage] = []
    for m in prior_messages:
        if m.role == MessageRole.USER:
            lc_history.append(HumanMessage(content=m.content))
        elif m.role == MessageRole.ASSISTANT:
            lc_history.append(AIMessage(content=m.content))

    # Persist the new user message.
    db.add(
        Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )
    )
    await db.flush()

    full_response = ""
    async for chunk in run_agent(
        merchant=merchant,
        history=lc_history,
        user_message=user_message,
        db=db,
    ):
        full_response += chunk
        yield chunk

    # Persist assistant response.
    db.add(
        Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=full_response,
        )
    )

    # Auto-title on the very first exchange.
    if not conv.title and not prior_messages:
        conv.title = user_message[:60]

    await db.flush()
