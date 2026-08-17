from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.bank_account_dto import BankAccountDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetBankAccountQuery(Query):
    actor: AuthenticatedActor
    bank_account_id: uuid.UUID


class GetBankAccountHandler(QueryHandler[GetBankAccountQuery, BankAccountDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetBankAccountQuery) -> BankAccountDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyBankAccountRepository(session)
            bank_account = await repo.get_by_id(query.bank_account_id)
        if bank_account is None:
            raise NotFoundError("FINANCIAL_BANK_ACCOUNT_NOT_FOUND", "Conta Bancária não encontrada.")
        return BankAccountDTO.from_entity(bank_account)
