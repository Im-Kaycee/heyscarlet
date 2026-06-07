from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
from datetime import datetime, timezone
import uuid
from sqlalchemy import update
from app.db.session import AsyncSessionLocal, get_session
from app.models.conversation import Conversation, Message, MessageRole
from app.models.user import User
from app.schemas.chat import ChatRequest, ConversationResponse, MessageResponse, CreateConversationRequest
from app.services.gemini import stream_scarlet_response
from app.core.dependencies import get_current_user
from app.services.memory import fetch_visible_memories, format_memory_context
router = APIRouter(prefix="/chat", tags=["chat"])


async def _get_memory_context(user_id: uuid.UUID, session: AsyncSession) -> str:
    """Pull stored user memories and format them for Scarlet's system prompt."""
    memories = await fetch_visible_memories(session, user_id)
    return format_memory_context(memories)


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

"""
    THIS IS FOR THE EVENT STREAM FUNCTION
    Generator function that streams Scarlet's response token by token to the client
    using Server-Sent Events (SSE) format.

    Flow:
    1. Calls Gemini and yields each token as it arrives, formatted as SSE data frames
    2. Once streaming is complete, opens a FRESH database session (separate from the
       request session) to persist the full assembled response as an assistant message
       and update the conversation's updated_at timestamp
    3. Yields a final [DONE] event so the client knows the stream has ended

    Why a new session? The conversation object is bound to the request session which
    closes after the route handler returns. By the time streaming finishes, that session
    is gone — so we open a new one just for the DB writes.
    """
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

        async with AsyncSessionLocal() as new_session:
            # Save assistant message
            assistant_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.assistant,
                content="".join(full_response),
            )
            new_session.add(assistant_msg)

            # Update conversation timestamp directly without re-adding the object
            await new_session.exec(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(updated_at=datetime.now(timezone.utc))
            )

            await new_session.commit()

        yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.exec(
        select(Conversation)
        .where(
            Conversation.user_id == current_user.id,
            Conversation.is_archived == False,
        )
        .order_by(Conversation.updated_at.desc())
    )
    return result.all()


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Verify conversation belongs to current user
    conv_result = await session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    if not conv_result.first():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return result.all()

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: CreateConversationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    conversation = Conversation(user_id=current_user.id, title=payload.title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@router.patch("/conversations/{conversation_id}/archive", response_model=ConversationResponse)
async def archive_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_archived = True
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation
