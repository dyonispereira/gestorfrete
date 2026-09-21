from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.financial_reversal_dto import FinancialReversalDTO
from modules.financial.domain.entities.financial_reversal import FinancialReversal
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_financial_reversal_repository import (
    SqlAlchemyFinancialReversalRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateFinancialReversalCommand(Command):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID | None
    accounts_payable_id: uuid.UUID | None
    accounts_receivable_id: uuid.UUID | None
    valor: Decimal
    motivo: str


class CreateFinancialReversalHandler(CommandHandler[CreateFinancialReversalCommand, FinancialReversalDTO]):
    """Auditoria #3 do usuário — D266: nunca altera `status`/`valor` do alvo, só insere o registro
    de correção. Publica `EstornoRealizado` (documentado, D270/EVENT_MAP.md) — não despachado a um
    EventBus real, mesma situação de todo lote anterior."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateFinancialReversalCommand) -> FinancialReversalDTO:
        FinancialReversal.check_target(
            fatura_id=command.invoice_id, conta_pagar_id=command.accounts_payable_id,
            conta_receber_id=command.accounts_receivable_id,
        )

        async with SQLAlchemyUnitOfWork() as uow:
            reversal_repo = SqlAlchemyFinancialReversalRepository(uow.session)

            if command.invoice_id is not None:
                if await SqlAlchemyInvoiceRepository(uow.session).get_by_id(command.invoice_id) is None:
                    raise NotFoundError("FINANCIAL_REVERSAL_TARGET_NOT_FOUND", "Fatura alvo não encontrada.")
            elif command.accounts_payable_id is not None:
                if await SqlAlchemyAccountsPayableRepository(uow.session).get_by_id(command.accounts_payable_id) is None:
                    raise NotFoundError("FINANCIAL_REVERSAL_TARGET_NOT_FOUND", "Conta a Pagar alvo não encontrada.")
            elif command.accounts_receivable_id is not None:
                if (
                    await SqlAlchemyAccountsReceivableRepository(uow.session).get_by_id(command.accounts_receivable_id)
                    is None
                ):
                    raise NotFoundError("FINANCIAL_REVERSAL_TARGET_NOT_FOUND", "Conta a Receber alvo não encontrada.")

            reversal = FinancialReversal.create(
                fatura_id=command.invoice_id, conta_pagar_id=command.accounts_payable_id,
                conta_receber_id=command.accounts_receivable_id, valor=command.valor, motivo=command.motivo,
                now=datetime.now(timezone.utc),
            )
            await reversal_repo.add(reversal)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="estornos_financeiros",
                entidade_id=reversal.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"valor": str(reversal.valor), "motivo": reversal.motivo},
            )

            await uow.commit()

        # `criado_por` vem direto do actor que acabou de executar o comando — sem precisar
        # reconsultar `logs_auditoria` (isso só é necessário em `Get`/`List`, que leem um Estorno
        # já existente sem ter o actor original em mãos).
        return FinancialReversalDTO.from_entity(reversal, criado_por=command.actor.user_id)
