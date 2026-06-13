from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from app.models.conversation import MessageRole


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str
class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    
# Pydantic schema to validate the incoming JSON from the frontend
class MemoryCreate(BaseModel):
    key: str
    value: str
    source: str = "onboarding"
    sensitivity_flag: bool = False
