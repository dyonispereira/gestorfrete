from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteBankAccountCommand(Command):
    actor: AuthenticatedActor
    bank_account_id: uuid.UUID


class DeleteBankAccountHandler(CommandHandler[DeleteBankAccountCommand, None]):
    """D394 — `FINANCIAL_BANK_ACCOUNT_IN_USE` nunca dispara nesta versão (sem `lancamentos_
    extrato_bancario`, D385); endpoint aceita, condição de bloqueio está sempre vazia."""

    async def handle(self, command: DeleteBankAccountCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyBankAccountRepository(uow.session)
            bank_account = await repo.get_by_id(command.bank_account_id)
            if bank_account is None:
                raise NotFoundError("FINANCIAL_BANK_ACCOUNT_NOT_FOUND", "Conta Bancária não encontrada.")

            bank_account.soft_delete(deleted_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(bank_account)
            await uow.commit()
