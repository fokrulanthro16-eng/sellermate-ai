import random
import string
import time

import jwt
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.merchant import Merchant
from app.schemas.auth import AuthResponse, LoginRequest, MerchantOut, RegisterRequest, TokenPair

settings = get_settings()

_REFRESH_KEY = "refresh:{merchant_id}"
_BLACKLIST_KEY = "blacklist:{token}"
_OTP_KEY = "otp:{phone}"


async def register(db: AsyncSession, redis: Redis, data: RegisterRequest) -> AuthResponse:
    result = await db.execute(
        select(Merchant).where(
            or_(Merchant.email == data.email, Merchant.phone == data.phone)
        )
    )
    if result.scalar_one_or_none():
        raise ConflictException("An account with this email or phone already exists")

    merchant = Merchant(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        business_name=data.business_name,
        owner_name=data.owner_name,
        business_type=data.business_type,
    )
    db.add(merchant)
    await db.flush()

    tokens = await _issue_tokens(redis, merchant.id)
    return AuthResponse(merchant=MerchantOut.model_validate(merchant), tokens=tokens)


async def login(db: AsyncSession, redis: Redis, data: LoginRequest) -> AuthResponse:
    result = await db.execute(
        select(Merchant).where(
            or_(Merchant.email == data.identifier, Merchant.phone == data.identifier)
        )
    )
    merchant = result.scalar_one_or_none()

    if not merchant or not verify_password(data.password, merchant.password_hash):
        raise UnauthorizedException("Invalid credentials")

    if merchant.status.value == "SUSPENDED":
        raise UnauthorizedException("Account suspended — contact support")

    tokens = await _issue_tokens(redis, merchant.id)
    return AuthResponse(merchant=MerchantOut.model_validate(merchant), tokens=tokens)


async def refresh_tokens(db: AsyncSession, redis: Redis, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    merchant_id: str = payload["sub"]
    key = _REFRESH_KEY.format(merchant_id=merchant_id)
    stored = await redis.get(key)

    if stored != refresh_token:
        raise UnauthorizedException("Refresh token revoked or already rotated")

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant or merchant.status.value == "SUSPENDED":
        raise UnauthorizedException("Account not found or suspended")

    await redis.delete(key)
    return await _issue_tokens(redis, merchant_id)


async def logout(redis: Redis, access_token: str, refresh_token: str | None = None) -> None:
    try:
        payload = decode_token(access_token)
        remaining_ttl = int(payload["exp"]) - int(time.time())
        if remaining_ttl > 0:
            key = _BLACKLIST_KEY.format(token=access_token)
            await redis.setex(key, remaining_ttl, "1")
    except jwt.PyJWTError:
        pass

    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            key = _REFRESH_KEY.format(merchant_id=payload["sub"])
            await redis.delete(key)
        except jwt.PyJWTError:
            pass


async def send_otp(db: AsyncSession, redis: Redis, phone: str) -> str:
    result = await db.execute(select(Merchant).where(Merchant.phone == phone))
    if not result.scalar_one_or_none():
        raise NotFoundException("No account found for this phone number")
    otp = "".join(random.choices(string.digits, k=settings.otp_length))
    key = _OTP_KEY.format(phone=phone)
    await redis.setex(key, settings.otp_expire_seconds, otp)
    # TODO: send via SMS gateway in production
    return otp


async def verify_otp(redis: Redis, phone: str, otp: str) -> bool:
    key = _OTP_KEY.format(phone=phone)
    stored = await redis.get(key)
    return bool(stored and stored == otp)


async def reset_password(
    db: AsyncSession, redis: Redis, phone: str, otp: str, new_password: str
) -> None:
    otp_key = _OTP_KEY.format(phone=phone)
    stored = await redis.get(otp_key)
    if not stored or stored != otp:
        raise BadRequestException("Invalid or expired OTP")
    await redis.delete(otp_key)

    result = await db.execute(select(Merchant).where(Merchant.phone == phone))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise BadRequestException("No account found for this phone number")

    merchant.password_hash = hash_password(new_password)
    refresh_key = _REFRESH_KEY.format(merchant_id=merchant.id)
    await redis.delete(refresh_key)


async def _issue_tokens(redis: Redis, merchant_id: str) -> TokenPair:
    access = create_access_token(merchant_id)
    refresh = create_refresh_token(merchant_id)
    key = _REFRESH_KEY.format(merchant_id=merchant_id)
    await redis.setex(key, settings.refresh_token_expire_seconds, refresh)
    return TokenPair(access_token=access, refresh_token=refresh)
