"""Redis cache wrapper'ı."""
from __future__ import annotations

from typing import Iterable

import redis.asyncio as aioredis

from ..config import get_settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            get_settings().redis_url, decode_responses=True
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def cache_get(key: str) -> str | None:
    return await get_redis().get(key)


async def cache_set(key: str, value: str, ttl: int | None = None) -> None:
    ttl = ttl if ttl is not None else get_settings().cache_ttl_seconds
    await get_redis().set(key, value, ex=ttl)


async def invalidate(patterns: Iterable[str]) -> int:
    """Verilen pattern'lere uyan tüm cache key'lerini sil."""
    r = get_redis()
    deleted = 0
    for pattern in patterns:
        if "*" in pattern:
            keys = [k async for k in r.scan_iter(match=pattern, count=200)]
            if keys:
                deleted += await r.delete(*keys)
        else:
            deleted += await r.delete(pattern)
    return deleted
