from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO
from modules.financial.domain.entities.accounts_receivable import AccountsReceivable
from modules.financial.domain.entities.receivable_status_history_entry import ReceivableStatusHistoryEntry
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_receivable_status_history_repository import (
    SqlAlchemyReceivableStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateAccountsReceivableCommand(Command):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID
    valor: Decimal
    data_vencimento: date


class CreateAccountsReceivableHandler(CommandHandler[CreateAccountsReceivableCommand, AccountsReceivableDTO]):
    """Adiciona uma parcela extra a uma Fatura já emitida — caso raro, a maioria nasce via `POST
    /faturas` (`033-accounts-receivable.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateAccountsReceivableCommand) -> AccountsReceivableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            invoice_repo = SqlAlchemyInvoiceRepository(uow.session)
            receivable_repo = SqlAlchemyAccountsReceivableRepository(uow.session)
            history_repo = SqlAlchemyReceivableStatusHistoryRepository(uow.session)

            if await invoice_repo.get_by_id(command.invoice_id) is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")

            existing = await receivable_repo.list_for_invoice(command.invoice_id)
            next_installment = max((r.numero_parcela for r in existing), default=0) + 1
            if await receivable_repo.exists_with_installment(command.invoice_id, next_installment):
                raise ConflictError(
                    "FINANCIAL_RECEIVABLE_INSTALLMENT_ALREADY_EXISTS", "Parcela já existe para esta Fatura."
                )

            receivable = AccountsReceivable.create(
                fatura_id=command.invoice_id, numero_parcela=next_installment, valor=command.valor,
                data_vencimento=command.data_vencimento,
            )
            await receivable_repo.add(receivable)

            now = datetime.now(timezone.utc)
            await history_repo.add(
                ReceivableStatusHistoryEntry.create(
                    conta_receber_id=receivable.id, status=ReceivableStatus.PENDENTE,
                    usuario_id=command.actor.user_id, now=now,
                )
            )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_receber",
                entidade_id=receivable.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"numero_parcela": receivable.numero_parcela, "valor": str(receivable.valor)},
            )

            await uow.commit()

        return AccountsReceivableDTO.from_entity(receivable)
