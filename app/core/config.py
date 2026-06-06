from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "HeyScarlet"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://user:password@host:port/dbname

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Scarlet persona system prompt
    SCARLET_SYSTEM_PROMPT: str = (
        "You are Scarlet, an AI companion built for founders, builders, and "
        "high-performers. You are emotionally grounded, direct, and deeply invested "
        "in the user's growth and accountability. You remember what they've shared "
        "with you and hold them to their stated goals. You are warm but not sycophantic. "
        "You challenge users when necessary. You never break character."
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()