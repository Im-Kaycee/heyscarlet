from typing import List
import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.conversation import MemoryStatus, UserMemory


async def fetch_visible_memories(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> List[UserMemory]:
    result = await session.exec(
        select(UserMemory)
        .where(
            UserMemory.user_id == user_id,
            UserMemory.status == MemoryStatus.active,
            UserMemory.sensitivity_flag == False,
        )
        .order_by(UserMemory.updated_at.desc(), UserMemory.created_at.desc())
    )
    return result.all()


def format_memory_context(memories: List[UserMemory]) -> str:
    if not memories:
        return ""

    return "\n".join(f"- {memory.key}: {memory.value}" for memory in memories)
