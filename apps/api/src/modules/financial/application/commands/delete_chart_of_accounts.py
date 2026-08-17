from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteChartOfAccountsCommand(Command):
    actor: AuthenticatedActor
    chart_of_accounts_id: uuid.UUID


class DeleteChartOfAccountsHandler(CommandHandler[DeleteChartOfAccountsCommand, None]):
    async def handle(self, command: DeleteChartOfAccountsCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyChartOfAccountsRepository(uow.session)
            account = await repo.get_by_id(command.chart_of_accounts_id)
            if account is None:
                raise NotFoundError("FINANCIAL_CHART_OF_ACCOUNTS_NOT_FOUND", "Conta do Plano de Contas não encontrada.")

            if await repo.has_active_children(account.id):
                raise ConflictError(
                    "FINANCIAL_CHART_OF_ACCOUNTS_HAS_ACTIVE_CHILDREN", "Existem contas filhas ativas."
                )
            if await repo.is_referenced_by_payables(account.id):
                raise ConflictError(
                    "FINANCIAL_CHART_OF_ACCOUNTS_IN_USE", "Conta referenciada por Contas a Pagar existentes."
                )

            account.soft_delete(deleted_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(account)
            await uow.commit()
