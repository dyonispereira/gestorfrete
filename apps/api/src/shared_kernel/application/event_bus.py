from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, TypeVar

from shared_kernel.domain.domain_event import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)
EventHandler = Callable[[TEvent], Awaitable[None]]


class EventBus(ABC):
    """Port for publishing and subscribing to domain events.

    The concrete implementation (``core/messaging`` + each module's
    ``infrastructure/messaging``) publishes events to RabbitMQ, allowing
    bounded contexts to react to what happens in other bounded contexts
    without depending on each other directly (Event-Driven Architecture).
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def subscribe(self, event_type: type[TEvent], handler: EventHandler[TEvent]) -> None: ...
