from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAccountsReceivableCommand(Command):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID
    accounts_receivable_id: uuid.UUID
    valor: Decimal | None
    data_vencimento: date | None


class UpdateAccountsReceivableHandler(CommandHandler[UpdateAccountsReceivableCommand, AccountsReceivableDTO]):
    async def handle(self, command: UpdateAccountsReceivableCommand) -> AccountsReceivableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAccountsReceivableRepository(uow.session)
            receivable = await repo.get_by_id(command.accounts_receivable_id)
            if receivable is None or receivable.fatura_id != command.invoice_id:
                raise NotFoundError("FINANCIAL_RECEIVABLE_NOT_FOUND", "Conta a Receber não encontrada.")

            receivable.update(valor=command.valor, data_vencimento=command.data_vencimento)
            await repo.add(receivable)
            await uow.commit()

        return AccountsReceivableDTO.from_entity(receivable)
