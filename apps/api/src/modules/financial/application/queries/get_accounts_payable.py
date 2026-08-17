from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAccountsPayableQuery(Query):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID


class GetAccountsPayableHandler(QueryHandler[GetAccountsPayableQuery, AccountsPayableDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAccountsPayableQuery) -> AccountsPayableDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAccountsPayableRepository(session)
            payable = await repo.get_by_id(query.accounts_payable_id)
        if payable is None:
            raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")
        return AccountsPayableDTO.from_entity(payable)
