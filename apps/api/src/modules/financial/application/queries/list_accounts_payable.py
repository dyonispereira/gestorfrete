from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAccountsPayableQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    origin: str | None = None
    supplier_id: uuid.UUID | None = None
    cost_center_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    chart_of_accounts_id: uuid.UUID | None = None
    accounting_period: date | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None


@dataclass(frozen=True)
class ListAccountsPayableResult:
    items: list[AccountsPayableDTO]
    total: int


class ListAccountsPayableHandler(QueryHandler[ListAccountsPayableQuery, ListAccountsPayableResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAccountsPayableQuery) -> ListAccountsPayableResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAccountsPayableRepository(session)
            payables, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, origin=query.origin,
                supplier_id=query.supplier_id, cost_center_id=query.cost_center_id, trip_id=query.trip_id,
                vehicle_id=query.vehicle_id, chart_of_accounts_id=query.chart_of_accounts_id,
                accounting_period=query.accounting_period,
                due_date_from=query.due_date_from, due_date_to=query.due_date_to,
            )
        return ListAccountsPayableResult(items=[AccountsPayableDTO.from_entity(p) for p in payables], total=total)
