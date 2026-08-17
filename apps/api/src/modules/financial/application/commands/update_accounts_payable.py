from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAccountsPayableCommand(Command):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID
    supplier_id: uuid.UUID | None
    cost_center_id: uuid.UUID | None
    valor: Decimal | None
    data_vencimento: date | None
    chart_of_accounts_id: uuid.UUID | None


class UpdateAccountsPayableHandler(CommandHandler[UpdateAccountsPayableCommand, AccountsPayableDTO]):
    async def handle(self, command: UpdateAccountsPayableCommand) -> AccountsPayableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAccountsPayableRepository(uow.session)
            payable = await repo.get_by_id(command.accounts_payable_id)
            if payable is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            payable.update(
                fornecedor_id=command.supplier_id, centro_custo_id=command.cost_center_id, valor=command.valor,
                data_vencimento=command.data_vencimento, plano_contas_id=command.chart_of_accounts_id,
                updated_by=command.actor.user_id, now=datetime.now(timezone.utc),
            )
            await repo.add(payable)
            await uow.commit()

        return AccountsPayableDTO.from_entity(payable)
