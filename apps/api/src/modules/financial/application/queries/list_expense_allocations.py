from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.expense_allocation_dto import ExpenseAllocationDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_allocation_repository import (
    SqlAlchemyExpenseAllocationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListExpenseAllocationsQuery(Query):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID


class ListExpenseAllocationsHandler(QueryHandler[ListExpenseAllocationsQuery, list[ExpenseAllocationDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListExpenseAllocationsQuery) -> list[ExpenseAllocationDTO]:
        async with self._session_factory() as session:
            payable_repo = SqlAlchemyAccountsPayableRepository(session)
            if await payable_repo.get_by_id(query.accounts_payable_id) is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            allocation_repo = SqlAlchemyExpenseAllocationRepository(session)
            allocations = await allocation_repo.list_for_payable(query.accounts_payable_id)
        return [ExpenseAllocationDTO.from_entity(a) for a in allocations]
