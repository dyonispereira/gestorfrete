from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.invoice_dto import InvoiceDTO
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
    fiscal (`009-FISCAL.md`, lote futuro) — não detalhado aqui."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CancelInvoiceCommand) -> InvoiceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyInvoiceRepository(uow.session)
            invoice = await repo.get_by_id(command.invoice_id)
            if invoice is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")

            invoice.cancel(cancelled_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(invoice)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="faturas", entidade_id=invoice.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": invoice.status.value},
            )

            await uow.commit()

        return InvoiceDTO.from_entity(invoice)
