from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType


class UnitOfWork(ABC):
    """Port that guarantees atomicity between repository writes and the
    domain events raised while handling a single Command.

    Concrete implementations wrap a SQLAlchemy ``AsyncSession`` and, on
    ``commit``, persist the aggregate changes and dispatch the recorded
    domain events within the same unit of work.
    """

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
