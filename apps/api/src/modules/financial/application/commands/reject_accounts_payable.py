from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.domain.entities.expense_approval import ExpenseApproval
from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry
from modules.financial.domain.value_objects.expense_approval_decision import ExpenseApprovalDecision
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_allocation_repository import (
    SqlAlchemyExpenseAllocationRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_approval_repository import (
    SqlAlchemyExpenseApprovalRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payable_status_history_repository import (
    SqlAlchemyPayableStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RejectAccountsPayableCommand(Command):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID
    justification: str


class RejectAccountsPayableHandler(CommandHandler[RejectAccountsPayableCommand, AccountsPayableDTO]):
    """`justification` obrigatória (D010). V1 Operational Hardening, Parte 1: rejeitar remove o
    Rateio da Conta a Pagar e recalcula `Trip.custo_realizado` da Viagem afetada — mesmo mecanismo
    de `DeleteAccountsPayableHandler` (D390/D393). Regra formal em `006-financeiro.md` (Conta a
    Pagar): regime de competência, `REJEITADA` é a única exclusão de `custo_realizado`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RejectAccountsPayableCommand) -> AccountsPayableDTO:
        if not command.justification or not command.justification.strip():
            raise ValidationError(
                "FINANCIAL_PAYABLE_JUSTIFICATION_REQUIRED", "justification é obrigatória para rejeitar."
            )

        async with SQLAlchemyUnitOfWork() as uow:
            payable_repo = SqlAlchemyAccountsPayableRepository(uow.session)
            approval_repo = SqlAlchemyExpenseApprovalRepository(uow.session)
            history_repo = SqlAlchemyPayableStatusHistoryRepository(uow.session)
            allocation_repo = SqlAlchemyExpenseAllocationRepository(uow.session)

            payable = await payable_repo.get_by_id(command.accounts_payable_id)
            if payable is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            trip_id = payable.allocation_target_trip_id
            payable.reject()
            await payable_repo.add(payable)
            await allocation_repo.delete_for_payable(payable.id)

            now = datetime.now(timezone.utc)
            await approval_repo.add(
                ExpenseApproval.create(
                    conta_pagar_id=payable.id, decisao=ExpenseApprovalDecision.REJEITADO,
                    justificativa=command.justification, ator_id=command.actor.user_id, now=now,
                )
            )
            await history_repo.add(
                PayableStatusHistoryEntry.create(
                    conta_pagar_id=payable.id, status=payable.status, usuario_id=command.actor.user_id, now=now,
                    observacao=command.justification,
                )
            )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_pagar", entidade_id=payable.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                motivo=command.justification,
            )

            new_realized_cost: Decimal | None = None
            if trip_id is not None:
                new_realized_cost = await allocation_repo.sum_for_trip(trip_id)

            await uow.commit()

        if trip_id is not None and new_realized_cost is not None:
            await TripInternalTransitions().update_realized_cost(trip_id=trip_id, value=new_realized_cost)

        return AccountsPayableDTO.from_entity(payable)
