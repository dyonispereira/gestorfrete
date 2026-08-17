from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.documents.application.dtos.mdfe_dto import MdfeDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListMdfesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    trip_id: uuid.UUID | None = None
    status: str | None = None
    series: str | None = None


@dataclass(frozen=True)
class ListMdfesResult:
    items: list[MdfeDTO]
    total: int


class ListMdfesHandler(QueryHandler[ListMdfesQuery, ListMdfesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListMdfesQuery) -> ListMdfesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyMdfeRepository(session)
            mdfes, total = await repo.list_page(
                page=query.page, limit=query.limit, viagem_id=query.trip_id, status=query.status,
                serie=query.series,
            )
            items = [MdfeDTO.from_entity(m, cte_ids=await repo.list_cte_ids(m.id)) for m in mdfes]
        return ListMdfesResult(items=items, total=total)
