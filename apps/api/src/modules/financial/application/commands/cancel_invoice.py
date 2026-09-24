from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.financial.application.dtos.invoice_dto import InvoiceDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CancelInvoiceCommand(Command):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID


class CancelInvoiceHandler(CommandHandler[CancelInvoiceCommand, InvoiceDTO]):
    """`EMITIDA→CANCELADA` — D273, único comando real de Fatura. Reabre necessidade de reemissão
    fiscal (`009-FISCAL.md`, lote futuro) — não detalhado aqui.

    Pilot Hardening Final, Parte 4: bloqueia o cancelamento se qualquer Conta a Receber já tiver
    `valor_recebido > 0`. `contas_receber_status_enum` é fechado por D273 (nunca ganha um status
    `CANCELADA` — corrigir uma CR já lançada é sempre Estorno, D266, nunca mutação direta de
    status). Como não existe um "CR cancelada" representável, a única forma de nunca fazer receita
    já recebida desaparecer silenciosamente é impedir o cancelamento da Fatura enquanto essa
    receita não for corrigida via Estorno primeiro. Só quando toda CR da Fatura ainda está
    PENDENTE/VENCIDA (nada recebido) o cancelamento segue sem tocar nenhuma CR."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CancelInvoiceCommand) -> InvoiceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyInvoiceRepository(uow.session)
            receivable_repo = SqlAlchemyAccountsReceivableRepository(uow.session)
            invoice = await repo.get_by_id(command.invoice_id)
            if invoice is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")

            receivables = await receivable_repo.list_for_invoice(invoice.id)
            received = [r for r in receivables if r.valor_recebido > 0]
            if received:
                parcelas = ", ".join(str(r.numero_parcela) for r in received)
                raise ConflictError(
                    "FINANCIAL_INVOICE_HAS_RECEIVED_RECEIVABLES",
                    "Não é possível cancelar a Fatura: a(s) parcela(s) "
                    f"{parcelas} já têm valor recebido. Corrija via Estorno (POST "
                    "/estornos-financeiros) antes de cancelar.",
                )

            invoice.cancel(cancelled_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(invoice)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="faturas", entidade_id=invoice.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": invoice.status.value},
            )

            await uow.commit()

        return InvoiceDTO.from_entity(invoice)
