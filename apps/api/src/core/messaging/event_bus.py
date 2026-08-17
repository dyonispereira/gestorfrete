from __future__ import annotations

import dataclasses
import datetime
import json
import logging
import uuid
from typing import Any

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

from core.messaging.rabbitmq_client import get_rabbitmq_connection
from shared_kernel.application.event_bus import EventBus, EventHandler, TEvent
from shared_kernel.domain.domain_event import DomainEvent

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "domain_events"
"""Single topic exchange shared by every bounded context (D032 — publishers
never know their consumers; RabbitMQ routing, not code, decides fan-out).
Routing key is always the event's class name (``ViagemCriada``,
``WebhookFalhou``, ...) — matching the exact names catalogued in
``docs/product/EVENT_MAP.md``, never invented ad hoc per module.
"""


def _json_default(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def serialize_event(event: DomainEvent) -> bytes:
    payload = dataclasses.asdict(event)
    payload["event_type"] = type(event).__name__
    return json.dumps(payload, default=_json_default).encode("utf-8")


class RabbitMQEventBus(EventBus):
    """RabbitMQ-backed implementation of the ``EventBus`` port.

    ``subscribe`` only registers the handler in-process — it does not, by
    itself, start consuming from RabbitMQ. A dedicated worker process (out of
    scope for this foundation lote, no domain event exists yet) calls
    ``start_consuming`` once, after every module has registered its handlers,
    to bind the actual AMQP queues and begin dispatching.
    """

    def __init__(self) -> None:
        self._connection: AbstractRobustConnection | None = None
        self._exchange: AbstractExchange | None = None
        self._handlers: dict[type[DomainEvent], list[EventHandler[Any]]] = {}

    async def connect(self) -> None:
        self._connection = await get_rabbitmq_connection()
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(self, event: DomainEvent) -> None:
        if self._exchange is None:
            raise RuntimeError("RabbitMQEventBus.connect() must be called before publish()")

        routing_key = type(event).__name__
        message = aio_pika.Message(
            body=serialize_event(event),
            content_type="application/json",
            message_id=str(event.event_id),
            timestamp=event.occurred_at,
        )
        await self._exchange.publish(message, routing_key=routing_key)
        logger.info("event_published", extra={"event_type": routing_key, "event_id": str(event.event_id)})

    def subscribe(self, event_type: type[TEvent], handler: EventHandler[TEvent]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
