from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    onboarding_complete: bool

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str