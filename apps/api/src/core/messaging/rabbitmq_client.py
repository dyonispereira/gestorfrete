from __future__ import annotations

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from core.config.settings import get_settings

_connection: AbstractRobustConnection | None = None


async def get_rabbitmq_connection() -> AbstractRobustConnection:
    """Returns a process-wide robust connection to RabbitMQ, the transport
    used by every bounded context to publish and consume domain events
    (Event-Driven Architecture). Created lazily on first use.
    """

    global _connection
    if _connection is None or _connection.is_closed:
        settings = get_settings()
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def close_rabbitmq_connection() -> None:
    """Called from the application lifespan on shutdown. `aio_pika`'s robust connection runs a
    background reconnection watchdog task that doesn't always finish cancelling synchronously
    within a short-lived event loop (e.g. Starlette `TestClient`'s per-instantiation portal loop,
    torn down right after lifespan shutdown fires) — surfaced only once RabbitMQ started running
    for real during tests (Backend Freeze), never before. Swallowed the same way
    `check_rabbitmq_connection` already treats any RabbitMQ-layer failure as non-fatal; the process
    is exiting either way, so a noisy cleanup race here is never a production correctness issue."""

    global _connection
    if _connection is not None and not _connection.is_closed:
        try:
            await _connection.close()
        except Exception:  # noqa: BLE001 — cleanup-time race in aio_pika's watchdog task, not ours
            pass
    _connection = None


async def check_rabbitmq_connection() -> bool:
    """Used by ``/health/ready`` — returns ``False`` instead of raising, same
    contract as ``core.database.session.check_database_connection``."""

    try:
        connection = await get_rabbitmq_connection()
        return not connection.is_closed
    except Exception:  # noqa: BLE001 — any failure means "not ready"
        return False
