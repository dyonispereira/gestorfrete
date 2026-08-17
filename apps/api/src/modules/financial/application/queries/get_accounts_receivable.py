from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAccountsReceivableQuery(Query):
    actor: AuthenticatedActor
    accounts_receivable_id: uuid.UUID


class GetAccountsReceivableHandler(QueryHandler[GetAccountsReceivableQuery, AccountsReceivableDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAccountsReceivableQuery) -> AccountsReceivableDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAccountsReceivableRepository(session)
            receivable = await repo.get_by_id(query.accounts_receivable_id)
        if receivable is None:
            raise NotFoundError("FINANCIAL_RECEIVABLE_NOT_FOUND", "Conta a Receber não encontrada.")
        return AccountsReceivableDTO.from_entity(receivable)
