from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.domain.entities.invoice_trip import InvoiceTrip
from modules.financial.domain.entities.receivable_status_history_entry import ReceivableStatusHistoryEntry
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_trip_repository import (
    SqlAlchemyInvoiceTripRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_receivable_status_history_repository import (
    SqlAlchemyReceivableStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_CENTS = Decimal("0.01")


def _allocate_realized_revenue_per_trip(
    total_received: Decimal, invoice_trips: list[InvoiceTrip], valor_bruto: Decimal
) -> list[tuple[uuid.UUID, Decimal]]:
    """Rateia `total_received` (recebido acumulado da Fatura inteira) entre as Viagens incluídas,
    proporcional ao `valor` de cada uma dentro de `valor_bruto`. A soma das alocações é **sempre
    exatamente** `total_received` — a última Viagem (ordem estável, `criado_em` asc) absorve o
    resto do arredondamento, nunca deixando a soma divergir do total realmente recebido (a Fatura
    agrupa Viagens, mas a receita nunca pode "dobrar" — pedido explícito do usuário). Chamado do
    zero a cada confirmação (nunca incrementado), então é idempotente e sempre consistente mesmo
    se `update_realized_revenue` for reprocessado."""

    if not invoice_trips:
        return []
    allocations: list[tuple[uuid.UUID, Decimal]] = []
    running = Decimal("0")
    for index, invoice_trip in enumerate(invoice_trips):
        if index == len(invoice_trips) - 1:
            share = total_received - running
        else:
            share = (total_received * invoice_trip.valor / valor_bruto).quantize(_CENTS, rounding=ROUND_HALF_UP)
            running += share
        allocations.append((invoice_trip.viagem_id, share))
    return allocations


@dataclass(frozen=True)
class ConfirmReceiptAccountsReceivableCommand(Command):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID
    accounts_receivable_id: uuid.UUID
    received_value: Decimal


class ConfirmReceiptAccountsReceivableHandler(
    CommandHandler[ConfirmReceiptAccountsReceivableCommand, AccountsReceivableDTO]
):
    """Auditoria #1 do usuário, continuação — D390: soma `valor_recebido` de todas as parcelas
    (inclusive `PARCIALMENTE_RECEBIDO`, Lote Financeiro Parte 2.1) da Fatura e chama
    `TripInternalTransitions.update_realized_revenue`; quando a **última** parcela deixa de ter
    saldo em aberto, chama também `record_financial_transition(RECEBIDA)` (D262/D390,
    `RecebimentoConfirmado`). Uma baixa parcial nunca dispara essa transição — só quando todas as
    parcelas da Fatura estão 100% recebidas.

    **Reconciliado (Lote Financeiro, Parte 3 — Faturamento Agrupado)**: uma Fatura pode cobrir N
    Viagens — o valor recebido é rateado entre elas (`_allocate_realized_revenue_per_trip`), nunca
    replicado integralmente em cada uma. No modo "por entrega" (sem `InvoiceTrip`), este bloco
    inteiro é pulado, exatamente como antes."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ConfirmReceiptAccountsReceivableCommand) -> AccountsReceivableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            invoice_repo = SqlAlchemyInvoiceRepository(uow.session)
            invoice_trip_repo = SqlAlchemyInvoiceTripRepository(uow.session)
            receivable_repo = SqlAlchemyAccountsReceivableRepository(uow.session)
            history_repo = SqlAlchemyReceivableStatusHistoryRepository(uow.session)

            invoice = await invoice_repo.get_by_id(command.invoice_id)
            if invoice is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")

            receivable = await receivable_repo.get_by_id(command.accounts_receivable_id)
            if receivable is None or receivable.fatura_id != command.invoice_id:
                raise NotFoundError("FINANCIAL_RECEIVABLE_NOT_FOUND", "Conta a Receber não encontrada.")

            now = datetime.now(timezone.utc)
            receivable.receive_payment(valor=command.received_value, now=now)
            await receivable_repo.add(receivable)

            await history_repo.add(
                ReceivableStatusHistoryEntry.create(
                    conta_receber_id=receivable.id, status=receivable.status, usuario_id=command.actor.user_id,
                    now=now,
                )
            )

            new_realized_revenue = await receivable_repo.sum_received_for_invoice(command.invoice_id)
            remaining_pending = await receivable_repo.count_pending_for_invoice(command.invoice_id)
            invoice_trips = await invoice_trip_repo.list_for_invoice(command.invoice_id)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_receber",
                entidade_id=receivable.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": receivable.status.value},
            )

            await uow.commit()

        allocations = _allocate_realized_revenue_per_trip(new_realized_revenue, invoice_trips, invoice.valor_bruto)
        for trip_id, share in allocations:
            await TripInternalTransitions().update_realized_revenue(trip_id=trip_id, value=share)
            if remaining_pending == 0:
                await TripInternalTransitions().record_financial_transition(
                    trip_id=trip_id, status=TripFinancialStatus.RECEBIDA, now=now
                )

        return AccountsReceivableDTO.from_entity(receivable)
