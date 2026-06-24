from typing import Callable

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.exceptions import RateLimitException
from app.db.redis import get_redis


def rate_limiter(key_prefix: str, max_calls: int, window_seconds: int) -> Callable:
    """
    Returns a FastAPI dependency that enforces a sliding-window rate limit.
    Key is scoped per IP + key_prefix. Raises HTTP 429 when exceeded.
    """
    async def _check(
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        redis_key = f"rl:{key_prefix}:{client_ip}"

        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, window_seconds)

        if count > max_calls:
            ttl = await redis.ttl(redis_key)
            retry_after = ttl if ttl > 0 else window_seconds
            raise RateLimitException(
                f"Too many requests. Try again in {retry_after} seconds.",
                retry_after=retry_after,
            )

    return _check
