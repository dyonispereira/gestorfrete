from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.cost_center_dto import CostCenterDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListCostCentersQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    branch_id: uuid.UUID | None = None
    search: str | None = None


@dataclass(frozen=True)
class ListCostCentersResult:
    items: list[CostCenterDTO]
    total: int


class ListCostCentersHandler(QueryHandler[ListCostCentersQuery, ListCostCentersResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListCostCentersQuery) -> ListCostCentersResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            cost_centers, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, branch_id=query.branch_id, search=query.search
            )
        return ListCostCentersResult(items=[CostCenterDTO.from_entity(c) for c in cost_centers], total=total)
