from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
from datetime import datetime
import uuid

from app.db.session import get_session
from app.models.conversation import Conversation, Message, MessageRole, UserMemory
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
    # NOTE for Ijudigal: inject current_user via get_current_user dependency
    # Replace hardcoded user_id below once auth dependency is ready
):
    # --- TEMPORARY: hardcoded user_id until auth dependency is wired ---
    # Ijudigal: replace this with: current_user: User = Depends(get_current_user)
    # then use current_user.id instead of TEMP_USER_ID
    TEMP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user_id = TEMP_USER_ID
    # -------------------------------------------------------------------

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
    current_user = Depends(get_current_user)
):
    # NOTE for Ijudigal: wire get_current_user here too
    # Stub for now — Nandom implements the full query
    statement = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.is_archived == False
    )
    
    # Execute asynchronously 
    result = await session.execute(statement)
    conversations = result.scalars().all()
    
    return conversations
    # raise HTTPException(status_code=501, detail="Implement list conversations")

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Verify the conversation exists AND belongs to this user
    convo_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    convo_result = await session.execute(convo_stmt)
    convo = convo_result.scalar_one_or_none()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Fetch the messages ordered by creation time
    msg_stmt = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc())
    
    msg_result = await session.execute(msg_stmt)
    messages = msg_result.scalars().all()
    
    return messages