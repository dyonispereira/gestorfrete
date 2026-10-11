from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.pricing.application.dtos.price_table_dto import PriceTableDTO
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListPriceTablesQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    direcao: str | None
    status: str | None
    cliente_id: uuid.UUID | None


@dataclass(frozen=True)
class ListPriceTablesResult:
    items: list[PriceTableDTO]
    total: int


class ListPriceTablesHandler(QueryHandler[ListPriceTablesQuery, ListPriceTablesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListPriceTablesQuery) -> ListPriceTablesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyPriceTableRepository(session)
            tables, total = await repo.list_page(
                page=query.page, limit=query.limit, direcao=query.direcao, status=query.status,
                cliente_id=query.cliente_id,
            )
        return ListPriceTablesResult(items=[PriceTableDTO.from_entity(t) for t in tables], total=total)
