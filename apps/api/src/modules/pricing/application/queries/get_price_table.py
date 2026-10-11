from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.pricing.application.dtos.price_table_dto import PriceTableDTO
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetPriceTableQuery(Query):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID


class GetPriceTableHandler(QueryHandler[GetPriceTableQuery, PriceTableDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetPriceTableQuery) -> PriceTableDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyPriceTableRepository(session)
            table = await repo.get_by_id(query.price_table_id)
        if table is None:
            raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")
        return PriceTableDTO.from_entity(table)
