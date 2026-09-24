from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.domain.entities.expense_allocation import ExpenseAllocation
from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_allocation_repository import (
    SqlAlchemyExpenseAllocationRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payable_status_history_repository import (
    SqlAlchemyPayableStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
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
    """Pilot Hardening Final, Parte 5: até aqui esta edição não gerava auditoria nem histórico
    (única exceção entre os comandos de `contas_pagar`) e, quando `valor` mudava, o Rateio de
    Despesa (D393) criado na origem continuava com o valor antigo — `Trip.custo_realizado` ficava
    dessincronizado do valor real editado. Corrigido: recria o Rateio com o novo valor e recalcula
    `custo_realizado` da mesma forma que `create`/`delete`/`reject` (D390)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateAccountsPayableCommand) -> AccountsPayableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAccountsPayableRepository(uow.session)
            history_repo = SqlAlchemyPayableStatusHistoryRepository(uow.session)
            allocation_repo = SqlAlchemyExpenseAllocationRepository(uow.session)

            payable = await repo.get_by_id(command.accounts_payable_id)
            if payable is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            valor_changed = command.valor is not None and command.valor != payable.valor
            now = datetime.now(timezone.utc)

            payable.update(
                fornecedor_id=command.supplier_id, centro_custo_id=command.cost_center_id, valor=command.valor,
                data_vencimento=command.data_vencimento, plano_contas_id=command.chart_of_accounts_id,
                updated_by=command.actor.user_id, now=now,
            )
            await repo.add(payable)

            trip_id = payable.allocation_target_trip_id
            new_realized_cost: Decimal | None = None
            has_allocation = trip_id is not None or payable.origem == PayableOrigin.ORDEM_SERVICO
            if valor_changed and has_allocation:
                await allocation_repo.delete_for_payable(payable.id)
                allocation = ExpenseAllocation.create(
                    conta_pagar_id=payable.id,
                    centro_custo_id=payable.centro_custo_id if trip_id is None else None,
                    viagem_id=trip_id, valor_rateado=payable.valor,
                )
                await allocation_repo.add(allocation)
                if trip_id is not None:
                    new_realized_cost = await allocation_repo.sum_for_trip(trip_id)

            await history_repo.add(
                PayableStatusHistoryEntry.create(
                    conta_pagar_id=payable.id, status=payable.status, usuario_id=command.actor.user_id, now=now,
                    observacao="Dados editados (Aguardando Aprovação).",
                )
            )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_pagar", entidade_id=payable.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"valor": str(payable.valor), "data_vencimento": payable.data_vencimento.isoformat()},
            )

            await uow.commit()

        if trip_id is not None and new_realized_cost is not None:
            await TripInternalTransitions().update_realized_cost(trip_id=trip_id, value=new_realized_cost)

        return AccountsPayableDTO.from_entity(payable)
