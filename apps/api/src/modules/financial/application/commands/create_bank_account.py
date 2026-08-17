from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.financial.application.dtos.bank_account_dto import BankAccountDTO
from modules.financial.domain.entities.bank_account import BankAccount
from modules.financial.domain.value_objects.bank_account_type import BankAccountType
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_bank_account_repository import (
    SqlAlchemyBankAccountRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateBankAccountCommand(Command):
    actor: AuthenticatedActor
    bank: str
    branch: str
    account_number: str
    tipo: BankAccountType


class CreateBankAccountHandler(CommandHandler[CreateBankAccountCommand, BankAccountDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateBankAccountCommand) -> BankAccountDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyBankAccountRepository(uow.session)

            if await repo.exists_with_numero_conta(command.account_number):
                raise ConflictError(
                    "FINANCIAL_BANK_ACCOUNT_NUMBER_ALREADY_EXISTS", "Já existe uma Conta Bancária com este número."
                )

            now = datetime.now(timezone.utc)
            bank_account = BankAccount.create(
                banco=command.bank, agencia=command.branch, numero_conta=command.account_number, tipo=command.tipo,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(bank_account)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="contas_bancarias",
                entidade_id=bank_account.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"banco": bank_account.banco, "numero_conta": bank_account.numero_conta},
            )

            await uow.commit()

        return BankAccountDTO.from_entity(bank_account)
