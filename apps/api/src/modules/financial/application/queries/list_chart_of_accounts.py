from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.chart_of_accounts_dto import ChartOfAccountsDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListChartOfAccountsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None
    tipo: str | None = None
    parent_id: uuid.UUID | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListChartOfAccountsResult:
    items: list[ChartOfAccountsDTO]
    total: int


class ListChartOfAccountsHandler(QueryHandler[ListChartOfAccountsQuery, ListChartOfAccountsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListChartOfAccountsQuery) -> ListChartOfAccountsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyChartOfAccountsRepository(session)
            accounts, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, tipo=query.tipo,
                parent_id=query.parent_id, status=query.status,
            )
        return ListChartOfAccountsResult(items=[ChartOfAccountsDTO.from_entity(a) for a in accounts], total=total)
