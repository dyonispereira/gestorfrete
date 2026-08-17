from __future__ import annotations

from typing import Any

from shared_kernel.application.query import Query, QueryHandler


class QueryHandlerNotRegisteredError(RuntimeError):
    """Raised when dispatching a Query with no handler registered for its type."""


class QueryHandlerAlreadyRegisteredError(RuntimeError):
    """Raised when two handlers try to register for the same Query type."""


class InMemoryQueryBus:
    """Process-local QueryBus: routes a Query to its single registered
    QueryHandler. Symmetric to ``InMemoryCommandBus`` — kept as a separate
    class (not a shared base) because commands and queries are conceptually
    distinct in CQRS and must never be dispatched through the same channel.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Query], QueryHandler[Any, Any]] = {}

    def register(self, query_type: type[Query], handler: QueryHandler[Any, Any]) -> None:
        if query_type in self._handlers:
            raise QueryHandlerAlreadyRegisteredError(
                f"A handler is already registered for {query_type.__name__}"
            )
        self._handlers[query_type] = handler

    async def dispatch(self, query: Query) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise QueryHandlerNotRegisteredError(
                f"No handler registered for {type(query).__name__}"
            )
        return await handler.handle(query)
