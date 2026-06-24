from redis.asyncio import Redis
from redis.asyncio import from_url as _from_url

from app.core.config import get_settings

settings = get_settings()

_redis: Redis | None = None


async def init_redis() -> None:
    await get_redis()


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        client = _from_url(settings.redis_url, decode_responses=True)
        if settings.is_production:
            _redis = client
        else:
            try:
                await client.ping()
                _redis = client
            except Exception:
                import fakeredis.aioredis
                _redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
