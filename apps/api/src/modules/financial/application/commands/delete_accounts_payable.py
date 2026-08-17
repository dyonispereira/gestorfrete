from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_allocation_repository import (
    SqlAlchemyExpenseAllocationRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteAccountsPayableCommand(Command):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID


class DeleteAccountsPayableHandler(CommandHandler[DeleteAccountsPayableCommand, None]):
    """Auditoria #1 do usuário, "remover item": exclui o(s) Rateio(s) associado(s) e recalcula
    `Trip.custo_realizado` da mesma forma que a criação (D390/D393)."""

    async def handle(self, command: DeleteAccountsPayableCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            payable_repo = SqlAlchemyAccountsPayableRepository(uow.session)
            allocation_repo = SqlAlchemyExpenseAllocationRepository(uow.session)

            payable = await payable_repo.get_by_id(command.accounts_payable_id)
            if payable is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            trip_id = payable.allocation_target_trip_id
            payable.soft_delete(deleted_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await payable_repo.add(payable)
            await allocation_repo.delete_for_payable(payable.id)

            new_realized_cost: Decimal | None = None
            if trip_id is not None:
                new_realized_cost = await allocation_repo.sum_for_trip(trip_id)

            await uow.commit()

        if trip_id is not None and new_realized_cost is not None:
            await TripInternalTransitions().update_realized_cost(trip_id=trip_id, value=new_realized_cost)
