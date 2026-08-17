from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetBankAccountBalanceQuery(Query):
    actor: AuthenticatedActor
    bank_account_id: uuid.UUID


@dataclass(frozen=True)
class BankAccountBalanceResult:
    bank_account_id: uuid.UUID
    balance: Decimal
    calculated_at: datetime


class GetBankAccountBalanceHandler(QueryHandler[GetBankAccountBalanceQuery, BankAccountBalanceResult]):
    """D263/D394 — saldo sempre derivado, agregado do tenant inteiro (sem `conta_bancaria_id` em
    `contas_pagar`/`contas_receber`)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetBankAccountBalanceQuery) -> BankAccountBalanceResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyBankAccountRepository(session)
            if await repo.get_by_id(query.bank_account_id) is None:
                raise NotFoundError("FINANCIAL_BANK_ACCOUNT_NOT_FOUND", "Conta Bancária não encontrada.")
            balance = await repo.calculate_tenant_balance()
        return BankAccountBalanceResult(
            bank_account_id=query.bank_account_id, balance=balance, calculated_at=datetime.now(timezone.utc)
        )
