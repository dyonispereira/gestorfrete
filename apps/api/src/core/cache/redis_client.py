from __future__ import annotations

from functools import lru_cache
from typing import cast

from redis.asyncio import Redis

from core.config.settings import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return cast(Redis, Redis.from_url(settings.redis_url, decode_responses=True))


async def reset_redis_client() -> None:
    """Mesmo padrão de `core.database.session.dispose_engine` — fecha a conexão pooled e limpa o
    cache do singleton, para que o próximo `get_redis_client()` construa um cliente novo no loop
    de eventos atual. `redis.asyncio.Redis` é vinculado ao loop em que foi criado (diferente do
    engine SQLAlchemy, que reabre conexões sob demanda mesmo depois de `dispose()`); sem isto,
    reusar o cliente cacheado depois que o loop de um teste anterior fechou levanta
    `RuntimeError: Event loop is closed`."""

    try:
        client = get_redis_client()
        await client.aclose()
    except Exception:  # noqa: BLE001 — best-effort close, o objetivo real é limpar o cache abaixo
        pass
    finally:
        get_redis_client.cache_clear()


async def check_redis_connection() -> bool:
    """Used by ``/health/ready`` — returns ``False`` instead of raising, same
    contract as ``core.database.session.check_database_connection``."""

    try:
        return bool(await get_redis_client().ping())
    except Exception:  # noqa: BLE001 — any failure means "not ready"
        return False
