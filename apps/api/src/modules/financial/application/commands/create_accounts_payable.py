from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ValidationError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.domain.entities.accounts_payable import AccountsPayable
from modules.financial.domain.entities.expense_allocation import ExpenseAllocation
from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.domain.value_objects.payable_status import PayableStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_expense_allocation_repository import (
    SqlAlchemyExpenseAllocationRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payable_status_history_repository import (
    SqlAlchemyPayableStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateAccountsPayableCommand(Command):
    actor: AuthenticatedActor
    supplier_id: uuid.UUID
    cost_center_id: uuid.UUID
    origem: PayableOrigin
    trip_id: uuid.UUID | None
    maintenance_order_id: uuid.UUID | None
    valor: Decimal
    data_vencimento: date
    chart_of_accounts_id: uuid.UUID


class CreateAccountsPayableHandler(CommandHandler[CreateAccountsPayableCommand, AccountsPayableDTO]):
    """Auditoria #1 do usuário: quando `origem` tem viagem associada, cria o Rateio automático
    (D393) e atualiza `Trip.custo_realizado` via `TripInternalTransitions` (D390) — soma de **todos**
    os rateios da viagem, nunca só o valor desta Conta a Pagar isolada."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateAccountsPayableCommand) -> AccountsPayableDTO:
        AccountsPayable.check_origin(
            command.origem, viagem_id=command.trip_id, ordem_servico_id=command.maintenance_order_id
        )

        async with SQLAlchemyUnitOfWork() as uow:
            payable_repo = SqlAlchemyAccountsPayableRepository(uow.session)
            history_repo = SqlAlchemyPayableStatusHistoryRepository(uow.session)
            allocation_repo = SqlAlchemyExpenseAllocationRepository(uow.session)
            supplier_repo = SqlAlchemySupplierRepository(uow.session)
            cost_center_repo = SqlAlchemyCostCenterRepository(uow.session)
            chart_repo = SqlAlchemyChartOfAccountsRepository(uow.session)
            trip_repo = SqlAlchemyTripRepository(uow.session)

            if await supplier_repo.get_by_id(command.supplier_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_SUPPLIER_ID", "Fornecedor inexistente.")
            if await cost_center_repo.get_by_id(command.cost_center_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_COST_CENTER_ID", "Centro de Custo inexistente.")
            if await chart_repo.get_by_id(command.chart_of_accounts_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_CHART_OF_ACCOUNTS_ID", "Conta do Plano de Contas inexistente.")
            if command.trip_id is not None and await trip_repo.get_by_id(command.trip_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_TRIP_ID", "Viagem inexistente.")

            now = datetime.now(timezone.utc)
            payable = AccountsPayable.create(
                fornecedor_id=command.supplier_id, centro_custo_id=command.cost_center_id, origem=command.origem,
                viagem_id=command.trip_id, ordem_servico_id=command.maintenance_order_id, valor=command.valor,
                data_vencimento=command.data_vencimento, plano_contas_id=command.chart_of_accounts_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await payable_repo.add(payable)

            await history_repo.add(
                PayableStatusHistoryEntry.create(
                    conta_pagar_id=payable.id, status=payable.status, usuario_id=command.actor.user_id, now=now,
                    observacao="LANCADA" if payable.status == PayableStatus.APROVADA else None,
                )
            )

            allocation_target_trip_id = payable.allocation_target_trip_id
            new_realized_cost: Decimal | None = None
            if allocation_target_trip_id is not None or command.origem == PayableOrigin.ORDEM_SERVICO:
                allocation = ExpenseAllocation.create(
                    conta_pagar_id=payable.id,
                    centro_custo_id=command.cost_center_id if allocation_target_trip_id is None else None,
                    viagem_id=allocation_target_trip_id, valor_rateado=command.valor,
                )
                await allocation_repo.add(allocation)
                if allocation_target_trip_id is not None:
                    new_realized_cost = await allocation_repo.sum_for_trip(allocation_target_trip_id)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_pagar", entidade_id=payable.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"origem": payable.origem.value, "valor": str(payable.valor)},
            )

            await uow.commit()

        if allocation_target_trip_id is not None and new_realized_cost is not None:
            await TripInternalTransitions().update_realized_cost(
                trip_id=allocation_target_trip_id, value=new_realized_cost
            )

        return AccountsPayableDTO.from_entity(payable)
