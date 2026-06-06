from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from app.db.session import get_session
from app.core.dependencies import get_current_user
from app.models.user import User, RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production (requires HTTPS)
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == payload.email))
    if result.first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create refresh token
    raw_refresh = create_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token=raw_refresh,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(refresh_token)
    await session.commit()

    set_refresh_cookie(response, raw_refresh)
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == payload.email))
    user = result.first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Revoke all existing refresh tokens for this user
    existing = await session.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False,
        )
    )
    for token in existing.all():
        token.is_revoked = True
        session.add(token)

    # Create new refresh token
    raw_refresh = create_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token=raw_refresh,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(refresh_token)
    await session.commit()

    set_refresh_cookie(response, raw_refresh)
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="No refresh token")

    result = await session.exec(
        select(RefreshToken).where(
            RefreshToken.token == raw_refresh,
            RefreshToken.is_revoked == False,
        )
    )
    refresh_token = result.first()

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    if refresh_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Rotate — revoke old, issue new
    refresh_token.is_revoked = True
    session.add(refresh_token)

    raw_new = create_refresh_token()
    new_refresh = RefreshToken(
        user_id=refresh_token.user_id,
        token=raw_new,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(new_refresh)
    await session.commit()

    set_refresh_cookie(response, raw_new)
    access_token = create_access_token(subject=str(refresh_token.user_id))
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        result = await session.exec(
            select(RefreshToken).where(RefreshToken.token == raw_refresh)
        )
        token = result.first()
        if token:
            token.is_revoked = True
            session.add(token)
            await session.commit()

    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user