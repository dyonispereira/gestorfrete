from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from core.cache.redis_client import check_redis_connection
from core.database.session import check_database_connection
from core.messaging.rabbitmq_client import check_rabbitmq_connection
from core.storage.minio_client import check_storage_connection

pytestmark = pytest.mark.integration
"""Requires ``docker compose -f infra/compose/docker-compose.yml up -d
postgres redis rabbitmq minio`` — run with ``pytest -m integration``. The
default ``pytest`` invocation (``-m "not integration"`` in CI) skips this
file entirely rather than failing when no infra is running, matching
``docs/backend/TESTING_STRATEGY.md``.
"""


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test() -> AsyncIterator[None]:
    """D383 — `test_postgres_is_reachable` uses the process-wide `lru_cache`d SQLAlchemy engine
    like every other integration test file, but this file (alone, until Lote 5's own test file
    happened to sort right after it alphabetically) never disposed it afterward — the pool kept
    connections bound to this test's now-closed event loop, crashing the very first Postgres-
    touching test in whichever file runs next. Same fixture every other integration test file
    already has.

    V1 Operational Hardening, Parte 6 — same class of bug, now for Redis: `test_redis_is_reachable`
    below is the only test in the whole suite that unconditionally calls `get_redis_client()`
    (via `check_redis_connection`) regardless of `Idempotency-Key` — exactly the D383 pattern
    repeating itself, caught because this file happens to sort right before
    `test_management_result_flow.py`/`test_operacao_flow.py`, whose idempotency tests are real
    Redis consumers and got `RuntimeError: Event loop is closed` from the stale cached client."""

    yield
    from core.cache.redis_client import reset_redis_client
    from core.database.session import dispose_engine

    await dispose_engine()
    await reset_redis_client()


async def test_postgres_is_reachable() -> None:
    assert await check_database_connection() is True


async def test_redis_is_reachable() -> None:
    assert await check_redis_connection() is True


async def test_rabbitmq_is_reachable() -> None:
    assert await check_rabbitmq_connection() is True


async def test_minio_is_reachable() -> None:
    assert await check_storage_connection() is True
