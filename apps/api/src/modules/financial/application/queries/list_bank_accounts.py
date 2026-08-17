from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.bank_account_dto import BankAccountDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListBankAccountsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    tipo: str | None = None


@dataclass(frozen=True)
class ListBankAccountsResult:
    items: list[BankAccountDTO]
    total: int


class ListBankAccountsHandler(QueryHandler[ListBankAccountsQuery, ListBankAccountsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListBankAccountsQuery) -> ListBankAccountsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyBankAccountRepository(session)
            accounts, total = await repo.list_page(page=query.page, limit=query.limit, status=query.status, tipo=query.tipo)
        return ListBankAccountsResult(items=[BankAccountDTO.from_entity(a) for a in accounts], total=total)
