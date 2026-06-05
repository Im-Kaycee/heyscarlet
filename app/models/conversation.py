from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    title: Optional[str] = Field(default=None)  # auto-generated from first message
    is_archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    conversation_id: uuid.UUID = Field(
        foreign_key="conversations.id", index=True, nullable=False
    )
    role: MessageRole = Field(nullable=False)
    content: str = Field(nullable=False)
    token_count: Optional[int] = Field(default=None)  # for usage tracking
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserMemory(SQLModel, table=True):
    """
    Stores structured memory extracted from user conversations.
    Used to inject context into Scarlet's system prompt.
    """
    __tablename__ = "user_memories"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    key: str = Field(nullable=False)    # e.g. "current_goal", "biggest_fear"
    value: str = Field(nullable=False)  # e.g. "Launch HeyScarlet by August"
    source: str = Field(default="onboarding")  # "onboarding" | "conversation"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)