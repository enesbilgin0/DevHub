"""Auth router — kayıt, giriş, refresh, logout, me."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from ...models import RefreshToken, User
from ..deps import CurrentUser, SessionDep
from ..schemas import LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_token_pair(session: SessionDep, user: User) -> TokenPair:
    access_token, access_exp = create_access_token(user.id)
    refresh_token, jti, refresh_exp = create_refresh_token(user.id)
    session.add(RefreshToken(jti=jti, user_id=user.id, expires_at=refresh_exp))
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_exp,
        refresh_expires_at=refresh_exp,
    )


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
    description="Username, email ve şifre ile yeni hesap oluşturur ve token çiftini döner.",
    responses={409: {"description": "Username veya email kullanımda"}},
)
async def register(payload: RegisterIn, session: SessionDep) -> TokenPair:
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        bio=payload.bio,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from None
    return await _issue_token_pair(session, user)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Giriş (JSON)",
    description="`identifier` username veya email olabilir. Başarılıysa access + refresh token döner.",
    responses={401: {"description": "Hatalı kimlik bilgisi"}},
)
async def login(payload: LoginIn, session: SessionDep) -> TokenPair:
    stmt = select(User).where(
        or_(User.username == payload.identifier, User.email == payload.identifier)
    )
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return await _issue_token_pair(session, user)


@router.post(
    "/token",
    response_model=TokenPair,
    summary="OAuth2 form-tabanlı giriş",
    description=(
        "Swagger UI'daki 'Authorize' butonu için OAuth2 password grant uyumlu endpoint."
        " Form alanları: `username`, `password`. Response /login ile aynıdır."
    ),
    responses={401: {"description": "Hatalı kimlik bilgisi"}},
)
async def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> TokenPair:
    return await login(LoginIn(identifier=form.username, password=form.password), session)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh token ile yeni access üret",
    description="Refresh token rotation: kullanılan jti revoke edilir, yeni jti üretilir.",
    responses={401: {"description": "Refresh token geçersiz veya süresi dolmuş"}},
)
async def refresh(payload: RefreshIn, session: SessionDep) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    jti = claims["jti"]
    user_id = int(claims["sub"])

    stored = (
        await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    ).scalar_one_or_none()
    if stored is None or stored.revoked or stored.expires_at < datetime.now(tz=UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired",
        )

    stored.revoked = True
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return await _issue_token_pair(session, user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Bu kullanıcının tüm refresh token'larını revoke et",
)
async def logout(current_user: CurrentUser, session: SessionDep) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Mevcut kullanıcının profili",
    responses={401: {"description": "Geçersiz veya eksik access token"}},
)
async def me(current_user: CurrentUser) -> User:
    return current_user
