from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.conversation import MemoryStatus


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    value: str
    source: str
    status: MemoryStatus
    sessions_since_surfaced: int
    created_at: datetime
    updated_at: datetime
