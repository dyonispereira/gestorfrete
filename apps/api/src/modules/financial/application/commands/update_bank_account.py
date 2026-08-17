from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.bank_account_dto import BankAccountDTO
from modules.financial.domain.value_objects.bank_account_status import BankAccountStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateBankAccountCommand(Command):
    actor: AuthenticatedActor
    bank_account_id: uuid.UUID
    bank: str | None
    branch: str | None
    status: BankAccountStatus | None


class UpdateBankAccountHandler(CommandHandler[UpdateBankAccountCommand, BankAccountDTO]):
    """D077-style: `account_number`/`type` imutáveis após criação — nunca aceitos aqui."""

    async def handle(self, command: UpdateBankAccountCommand) -> BankAccountDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyBankAccountRepository(uow.session)
            bank_account = await repo.get_by_id(command.bank_account_id)
            if bank_account is None:
                raise NotFoundError("FINANCIAL_BANK_ACCOUNT_NOT_FOUND", "Conta Bancária não encontrada.")

            bank_account.update(
                banco=command.bank, agencia=command.branch, status=command.status, updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(bank_account)
            await uow.commit()

        return BankAccountDTO.from_entity(bank_account)
