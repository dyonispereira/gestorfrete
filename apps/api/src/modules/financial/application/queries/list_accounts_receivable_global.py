from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListAccountsReceivableGlobalQuery(Query):
    """Consulta agregada entre Faturas (Lote Financeiro, Parte 2.1) — distinta de
    `ListAccountsReceivableQuery` (Parte 2), que só lista as parcelas de UMA Fatura já conhecida.
    Ownership não muda: Conta a Receber continua sub-recurso de Fatura (D260)."""

    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    client_id: uuid.UUID | None = None
    accounting_period: date | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None


@dataclass(frozen=True)
class ListAccountsReceivableGlobalResult:
    items: list[AccountsReceivableDTO]
    total: int


class ListAccountsReceivableGlobalHandler(
    QueryHandler[ListAccountsReceivableGlobalQuery, ListAccountsReceivableGlobalResult]
):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListAccountsReceivableGlobalQuery) -> ListAccountsReceivableGlobalResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAccountsReceivableRepository(session)
            rows, total = await repo.list_page(
                page=query.page, limit=query.limit, status=query.status, client_id=query.client_id,
                accounting_period=query.accounting_period, due_date_from=query.due_date_from,
                due_date_to=query.due_date_to,
            )
        return ListAccountsReceivableGlobalResult(
            items=[AccountsReceivableDTO.from_entity(r, cliente_id=client_id) for r, client_id in rows], total=total
        )
