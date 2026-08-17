from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAccountsReceivableQuery(Query):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID


class ListAccountsReceivableHandler(QueryHandler[ListAccountsReceivableQuery, list[AccountsReceivableDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAccountsReceivableQuery) -> list[AccountsReceivableDTO]:
        async with self._session_factory() as session:
            invoice_repo = SqlAlchemyInvoiceRepository(session)
            if await invoice_repo.get_by_id(query.invoice_id) is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")

            receivable_repo = SqlAlchemyAccountsReceivableRepository(session)
            receivables = await receivable_repo.list_for_invoice(query.invoice_id)
        return [AccountsReceivableDTO.from_entity(r) for r in receivables]
