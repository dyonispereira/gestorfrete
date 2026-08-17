from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListDriversQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    employment_type: str | None = None
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


@dataclass(frozen=True)
class ListDriversResult:
    items: list[DriverDTO]
    total: int


class ListDriversHandler(QueryHandler[ListDriversQuery, ListDriversResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListDriversQuery) -> ListDriversResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyDriverRepository(session)
            drivers, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                status=query.status,
                employment_type=query.employment_type,
                search=query.search,
                created_from=query.created_from,
                created_to=query.created_to,
            )
        return ListDriversResult(items=[DriverDTO.from_entity(d) for d in drivers], total=total)
