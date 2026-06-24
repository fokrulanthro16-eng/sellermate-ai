from typing import Annotated

import jwt
from fastapi import Depends, Header
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.session import get_db
from app.db.redis import get_redis
from app.models.merchant import Merchant

_BLACKLIST_PREFIX = "blacklist:"


async def get_current_merchant(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Merchant:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token expired")
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid access token")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    if await redis.exists(f"{_BLACKLIST_PREFIX}{token}"):
        raise UnauthorizedException("Token has been revoked")

    merchant_id: str = payload["sub"]
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise UnauthorizedException("Account not found")
    if merchant.status.value == "SUSPENDED":
        raise UnauthorizedException("Account suspended — contact support")

    return merchant


# Convenience aliases used in every router
CurrentMerchant = Annotated[Merchant, Depends(get_current_merchant)]
DB = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]
