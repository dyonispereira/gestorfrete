from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database.session import get_session_factory
from shared_kernel.infrastructure.unit_of_work import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Concrete ``UnitOfWork`` wrapping a single ``AsyncSession``.

    One instance is created per Command handled (never shared across
    requests/commands) — repositories constructed inside the ``async with``
    block all share ``self.session``, so every write they perform is part of
    the same PostgreSQL transaction, committed or rolled back atomically by
    ``__aexit__`` (inherited from the base ``UnitOfWork``).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()
        self.session: AsyncSession = self._session_factory()

    async def __aenter__(self) -> Self:
        # Sobrescreve o retorno de `UnitOfWork.__aenter__` (tipado como a base abstrata) para o
        # tipo concreto — sem isso, `async with SQLAlchemyUnitOfWork() as uow: uow.session` falha
        # no `mypy --strict` (achado real deste lote, não apenas estilístico).
        return self

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc, traceback)
        finally:
            await self.session.close()
