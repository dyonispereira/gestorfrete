from __future__ import annotations

from typing import TypeVar

from shared_kernel.domain.base_entity import BaseEntity
from shared_kernel.domain.domain_event import DomainEvent

TId = TypeVar("TId")


class BaseAggregateRoot(BaseEntity[TId]):
    """Base class for every Aggregate Root in the system.

    An Aggregate Root is the single entry point of an aggregate: repositories
    only ever load/save aggregate roots, never the entities/value objects
    inside them. It is also responsible for recording the domain events
    raised while its invariants were enforced, so the application layer can
    dispatch them to the event bus after the transaction commits.
    """

    def __init__(self, id: TId) -> None:
        super().__init__(id)
        self._domain_events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_domain_events(self) -> list[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
