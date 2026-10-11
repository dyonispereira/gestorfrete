from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.pricing.application.dtos.price_table_dto import PriceTableItemDTO
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListPriceTableItemsQuery(Query):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID


class ListPriceTableItemsHandler(QueryHandler[ListPriceTableItemsQuery, list[PriceTableItemDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListPriceTableItemsQuery) -> list[PriceTableItemDTO]:
        async with self._session_factory() as session:
            repo = SqlAlchemyPriceTableRepository(session)
            items = await repo.get_items(query.price_table_id)
        return [PriceTableItemDTO.from_entity(i) for i in items]
