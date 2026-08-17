from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TResult = TypeVar("TResult")


class Query(ABC):
    """Marker base class for every Query (CQRS read side).

    A Query never changes the state of the system. Query handlers are free
    to bypass the domain model entirely and read straight from
    infrastructure/persistence when that is more efficient for the
    presentation need being served.
    """


TQuery = TypeVar("TQuery", bound=Query)


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Base class for the handler that executes a single Query."""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult: ...
