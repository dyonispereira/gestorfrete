from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.cost_center_dto import CostCenterDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetCostCenterQuery(Query):
    actor: AuthenticatedActor
    cost_center_id: uuid.UUID


class GetCostCenterHandler(QueryHandler[GetCostCenterQuery, CostCenterDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetCostCenterQuery) -> CostCenterDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            cost_center = await repo.get_by_id(query.cost_center_id)
        if cost_center is None:
            raise NotFoundError("FINANCIAL_COST_CENTER_NOT_FOUND", "Centro de Custo não encontrado.")
        return CostCenterDTO.from_entity(cost_center)
