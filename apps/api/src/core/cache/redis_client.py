from __future__ import annotations

from functools import lru_cache
from typing import cast

from redis.asyncio import Redis

from core.config.settings import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return cast(Redis, Redis.from_url(settings.redis_url, decode_responses=True))


async def check_redis_connection() -> bool:
    """Used by ``/health/ready`` — returns ``False`` instead of raising, same
    contract as ``core.database.session.check_database_connection``."""

    try:
        return bool(await get_redis_client().ping())
    except Exception:  # noqa: BLE001 — any failure means "not ready"
        return False
