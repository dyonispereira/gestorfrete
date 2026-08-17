from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for every domain event in the system.

    A domain event is an immutable fact that already happened in the domain.
    Bounded contexts publish these to the event bus (RabbitMQ) so other
    bounded contexts can react without being directly coupled to each other.
    """

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: uuid.UUID | None = None
