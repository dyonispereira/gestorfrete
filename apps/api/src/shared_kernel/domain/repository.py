from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot
from shared_kernel.domain.specification import Specification

TAggregate = TypeVar("TAggregate", bound=BaseAggregateRoot[Any])
TId = TypeVar("TId")


class Repository(ABC, Generic[TAggregate, TId]):
    """Port for loading/persisting a single Aggregate Root (Repository Pattern).

    One concrete implementation per (module, aggregate) pair lives in that
    module's ``infrastructure/persistence/repositories`` — never a generic
    catch-all repository shared across bounded contexts, and never a
    repository for anything that is not an Aggregate Root (D237 — internal
    entities are only reachable through their owning aggregate).

    Every method is implicitly tenant-scoped: concrete implementations read
    ``core.multitenancy.context.get_current_tenant_id()`` themselves, so no
    caller ever passes a ``tenant_id`` parameter here (no repository accepts
    it, matching D208 at the persistence boundary too).
    """

    @abstractmethod
    async def get_by_id(self, id: TId) -> TAggregate | None: ...

    @abstractmethod
    async def add(self, aggregate: TAggregate) -> None: ...

    @abstractmethod
    async def find(self, specification: Specification[TAggregate]) -> list[TAggregate]: ...
