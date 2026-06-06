from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
from datetime import datetime
import uuid

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.conversation import Conversation, Message, MessageRole, UserMemory
from app.models.user import User
from app.schemas.chat import ChatRequest, ConversationResponse, MessageResponse
from app.services.gemini import stream_scarlet_response

router = APIRouter(prefix="/chat", tags=["chat"])


async def _get_memory_context(user_id: uuid.UUID, session: AsyncSession) -> str:
    """Pull stored user memories and format them for Scarlet's system prompt."""
    result = await session.exec(
        select(UserMemory).where(UserMemory.user_id == user_id)
    )
    memories = result.all()
    if not memories:
        return ""
    return "\n".join([f"- {m.key}: {m.value}" for m in memories])


async def _get_conversation_history(
    conversation_id: uuid.UUID, session: AsyncSession
) -> List[dict]:
    """Fetch prior messages for a conversation to pass as Gemini history."""
    result = await session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.all()
    return [{"role": msg.role.value, "content": msg.content} for msg in messages]


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    # Create or fetch conversation
    if payload.conversation_id:
        result = await session.exec(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # Fetch history and memory
    history = await _get_conversation_history(conversation.id, session)
    memory_context = await _get_memory_context(user_id, session)

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.user,
        content=payload.message,
    )
    session.add(user_msg)
    await session.commit()

    # Stream Scarlet's response
    full_response = []

    async def event_stream():
        async for token in stream_scarlet_response(
            user_message=payload.message,
            history=history,
            memory_context=memory_context,
        ):
            full_response.append(token)
            yield f"data: {token}\n\n"

        # After streaming completes, persist Scarlet's full response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.assistant,
            content="".join(full_response),
        )
        session.add(assistant_msg)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        await session.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    session: AsyncSession = Depends(get_session),
):
    # NOTE for Ijudigal: wire get_current_user here too
    # Stub for now — Nandom implements the full query
    raise HTTPException(status_code=501, detail="Implement list conversations")


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    # NOTE for Nandom: implement this — fetch messages for a conversation
    raise HTTPException(status_code=501, detail="Implement get messages")
