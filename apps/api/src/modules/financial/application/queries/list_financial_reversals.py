from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.financial_reversal_dto import FinancialReversalDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_financial_reversal_repository import (
    SqlAlchemyFinancialReversalRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListFinancialReversalsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    invoice_id: uuid.UUID | None = None
    accounts_payable_id: uuid.UUID | None = None
    accounts_receivable_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ListFinancialReversalsResult:
    items: list[FinancialReversalDTO]
    total: int


class ListFinancialReversalsHandler(QueryHandler[ListFinancialReversalsQuery, ListFinancialReversalsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListFinancialReversalsQuery) -> ListFinancialReversalsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyFinancialReversalRepository(session)
            reversals, total = await repo.list_page(
                page=query.page, limit=query.limit, invoice_id=query.invoice_id,
                accounts_payable_id=query.accounts_payable_id,
                accounts_receivable_id=query.accounts_receivable_id,
            )
        return ListFinancialReversalsResult(
            items=[FinancialReversalDTO.from_entity(r) for r in reversals], total=total
        )
