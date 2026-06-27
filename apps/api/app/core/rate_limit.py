import ipaddress
from typing import Callable

import jwt
from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.exceptions import RateLimitException
from app.db.redis import get_redis


def _get_client_ip(request: Request, trusted_cidrs: list[str]) -> str:
    """
    Return the real client IP, honoring X-Forwarded-For / CF-Connecting-IP only
    when the direct TCP connection originates from a configured trusted proxy CIDR.

    Without trusted CIDRs (the default), request.client.host is always used so
    clients cannot spoof their IP by injecting X-Forwarded-For headers.
    """
    direct_ip = request.client.host if request.client else None
    if not direct_ip:
        return "unknown"

    if not trusted_cidrs:
        return direct_ip

    try:
        direct_addr = ipaddress.ip_address(direct_ip)
    except ValueError:
        return direct_ip

    is_trusted = any(
        direct_addr in ipaddress.ip_network(cidr, strict=False)
        for cidr in trusted_cidrs
    )
    if not is_trusted:
        return direct_ip

    # Cloudflare sets CF-Connecting-IP to the original client IP (single value, no spoofing).
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if cf_ip:
        return cf_ip

    # Generic proxy: take the leftmost entry of X-Forwarded-For (the original client).
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip()

    return direct_ip


def rate_limiter(key_prefix: str, max_calls: int, window_seconds: int) -> Callable:
    """
    IP-scoped sliding-window rate limiter for public/unauthenticated endpoints.
    The effective client IP is resolved via _get_client_ip, which only trusts
    proxy headers (X-Forwarded-For, CF-Connecting-IP) when the connection arrives
    from a CIDR listed in TRUSTED_PROXY_CIDRS.
    """
    async def _check(
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        from app.core.config import get_settings
        client_ip = _get_client_ip(request, get_settings().trusted_proxy_cidr_list)
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


def merchant_rate_limiter(key_prefix: str, max_calls: int, window_seconds: int) -> Callable:
    """
    Per-merchant sliding-window rate limiter for authenticated AI endpoints.
    Decodes the Bearer JWT (sub claim) without a DB round-trip so limits are
    enforced per account and cannot be bypassed by rotating IPs or proxies.
    Auth failure (invalid/missing token) is left for the route's own dependency.
    """
    async def _check(
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        from app.core.security import decode_token

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return  # Missing token — auth dependency will reject the request

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = decode_token(token)
            merchant_id: str = payload.get("sub", "")
        except jwt.PyJWTError:
            return  # Invalid token — auth dependency will reject the request

        if not merchant_id:
            return

        redis_key = f"rl:{key_prefix}:{merchant_id}"
        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, window_seconds)

        if count > max_calls:
            ttl = await redis.ttl(redis_key)
            retry_after = ttl if ttl > 0 else window_seconds
            raise RateLimitException(
                f"AI request limit reached. Try again in {retry_after} seconds.",
                retry_after=retry_after,
            )

    return _check
