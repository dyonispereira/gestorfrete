from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.financial.application.dtos.chart_of_accounts_dto import ChartOfAccountsDTO
from modules.financial.domain.entities.chart_of_accounts import ChartOfAccounts
from modules.financial.domain.value_objects.chart_of_accounts_type import ChartOfAccountsType
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateChartOfAccountsCommand(Command):
    actor: AuthenticatedActor
    account_code: str
    name: str
    tipo: ChartOfAccountsType
    parent_id: uuid.UUID | None


class CreateChartOfAccountsHandler(CommandHandler[CreateChartOfAccountsCommand, ChartOfAccountsDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateChartOfAccountsCommand) -> ChartOfAccountsDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyChartOfAccountsRepository(uow.session)

            if await repo.exists_with_codigo(command.account_code):
                raise ConflictError(
                    "FINANCIAL_CHART_OF_ACCOUNTS_CODE_ALREADY_EXISTS", "Já existe uma conta com este código contábil."
                )
            if command.parent_id is not None and await repo.get_by_id(command.parent_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_CHART_OF_ACCOUNTS_ID", "Conta-pai inexistente.")

            now = datetime.now(timezone.utc)
            account = ChartOfAccounts.create(
                codigo_contabil=command.account_code, nome=command.name, tipo=command.tipo,
                categoria_pai_id=command.parent_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(account)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="plano_contas", entidade_id=account.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"codigo_contabil": account.codigo_contabil, "nome": account.nome},
            )

            await uow.commit()

        return ChartOfAccountsDTO.from_entity(account)
