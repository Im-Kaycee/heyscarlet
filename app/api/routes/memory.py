from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import UserMemory, MemoryStatus
from app.schemas.chat import MemoryCreate

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("", response_model=List[UserMemory])
async def get_user_memories(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    GET /memory: Returns active, non-sensitive memories for the current user.

    Filters:
    - status == active: Latent memories (recently surfaced) are excluded
    - sensitivity_flag == False: Sensitive memories require special handling
    """
    result = await session.exec(
        select(UserMemory).where(
            UserMemory.user_id == current_user.id,
            UserMemory.status == MemoryStatus.active,
            UserMemory.sensitivity_flag == False,
        )
    )
    return result.all()


# /memory endpoint to create or update a user memory
@router.post("", response_model=UserMemory, status_code=status.HTTP_200_OK)
async def save_or_update_memory(
    data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    POST /memory: Upsert a fact Scarlet learns about the user.
    Ensures one unique row per concept key per user.
    """
    # Step A: Check if a memory with that key already exists for the current user
    statement = select(UserMemory).where(
        UserMemory.user_id == current_user.id, 
        UserMemory.key == data.key
    )
    result = await session.exec(statement)
    existing_memory = result.first()

    if existing_memory:
        # Step B: If it exists — update value, reset status to active, update timestamps
        existing_memory.value = data.value
        existing_memory.source = data.source
        existing_memory.sensitivity_flag = data.sensitivity_flag
        existing_memory.status = MemoryStatus.active
        existing_memory.updated_at = datetime.utcnow()
        
        session.add(existing_memory)
        await session.commit()
        await session.refresh(existing_memory)
        return existing_memory

    # Step C: If it doesn't exist — create a new UserMemory row
    new_memory = UserMemory(
        user_id=current_user.id,
        key=data.key,
        value=data.value,
        source=data.source,
        sensitivity_flag=data.sensitivity_flag,
        status=MemoryStatus.active
    )
    session.add(new_memory)
    await session.commit()
    await session.refresh(new_memory)
    return new_memory