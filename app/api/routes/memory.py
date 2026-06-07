from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.memory import MemoryResponse
from app.services.memory import fetch_visible_memories

router = APIRouter(tags=["memory"])


@router.get("/memory", response_model=List[MemoryResponse])
async def get_memory(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await fetch_visible_memories(session, current_user.id)
