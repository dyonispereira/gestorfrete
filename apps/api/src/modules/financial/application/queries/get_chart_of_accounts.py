from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.chart_of_accounts_dto import ChartOfAccountsDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetChartOfAccountsQuery(Query):
    actor: AuthenticatedActor
    chart_of_accounts_id: uuid.UUID


class GetChartOfAccountsHandler(QueryHandler[GetChartOfAccountsQuery, ChartOfAccountsDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetChartOfAccountsQuery) -> ChartOfAccountsDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyChartOfAccountsRepository(session)
            account = await repo.get_by_id(query.chart_of_accounts_id)
        if account is None:
            raise NotFoundError("FINANCIAL_CHART_OF_ACCOUNTS_NOT_FOUND", "Conta do Plano de Contas não encontrada.")
        return ChartOfAccountsDTO.from_entity(account)
