from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.domain.entities.payable_status_history_entry import PayableStatusHistoryEntry
from modules.financial.domain.value_objects.bank_account_status import BankAccountStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payable_status_history_repository import (
    SqlAlchemyPayableStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class PayAccountsPayableCommand(Command):
    actor: AuthenticatedActor
    accounts_payable_id: uuid.UUID
    bank_account_id: uuid.UUID


class PayAccountsPayableHandler(CommandHandler[PayAccountsPayableCommand, AccountsPayableDTO]):
    """`APROVADA→PAGA` — o "pagamento" pedido no kickoff (`032-accounts-payable.md`). D394:
    `bank_account_id` só validado (existe e está `ATIVA`), não persistido — `contas_pagar` não tem
    coluna `conta_bancaria_id` na DDL congelada."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: PayAccountsPayableCommand) -> AccountsPayableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            payable_repo = SqlAlchemyAccountsPayableRepository(uow.session)
            bank_account_repo = SqlAlchemyBankAccountRepository(uow.session)
            history_repo = SqlAlchemyPayableStatusHistoryRepository(uow.session)

            payable = await payable_repo.get_by_id(command.accounts_payable_id)
            if payable is None:
                raise NotFoundError("FINANCIAL_PAYABLE_NOT_FOUND", "Conta a Pagar não encontrada.")

            bank_account = await bank_account_repo.get_by_id(command.bank_account_id)
            if bank_account is None:
                raise ValidationError("FINANCIAL_UNKNOWN_BANK_ACCOUNT_ID", "Conta Bancária inexistente.")
            if bank_account.status != BankAccountStatus.ATIVA:
                raise ValidationError("FINANCIAL_BANK_ACCOUNT_INACTIVE", "Conta Bancária está inativa.")

            payable.pay()
            await payable_repo.add(payable)

            await history_repo.add(
                PayableStatusHistoryEntry.create(
                    conta_pagar_id=payable.id, status=payable.status, usuario_id=command.actor.user_id,
                    now=datetime.now(timezone.utc),
                )
            )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_pagar", entidade_id=payable.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": payable.status.value},
            )

            await uow.commit()

        return AccountsPayableDTO.from_entity(payable)
