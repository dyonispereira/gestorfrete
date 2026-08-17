from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError, ValidationError
from modules.financial.application.dtos.chart_of_accounts_dto import ChartOfAccountsDTO
from modules.financial.domain.value_objects.chart_of_accounts_status import ChartOfAccountsStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_chart_of_accounts_repository import (
    SqlAlchemyChartOfAccountsRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateChartOfAccountsCommand(Command):
    actor: AuthenticatedActor
    chart_of_accounts_id: uuid.UUID
    name: str | None
    parent_id: uuid.UUID | None
    status: ChartOfAccountsStatus | None


class UpdateChartOfAccountsHandler(CommandHandler[UpdateChartOfAccountsCommand, ChartOfAccountsDTO]):
    async def handle(self, command: UpdateChartOfAccountsCommand) -> ChartOfAccountsDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyChartOfAccountsRepository(uow.session)
            account = await repo.get_by_id(command.chart_of_accounts_id)
            if account is None:
                raise NotFoundError("FINANCIAL_CHART_OF_ACCOUNTS_NOT_FOUND", "Conta do Plano de Contas não encontrada.")

            if command.parent_id is not None:
                if await repo.get_by_id(command.parent_id) is None:
                    raise ValidationError("FINANCIAL_UNKNOWN_CHART_OF_ACCOUNTS_ID", "Conta-pai inexistente.")
                if command.parent_id == account.id or await repo.is_descendant_of(account.id, command.parent_id):
                    raise DomainError(
                        "FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED",
                        "A nova conta-pai não pode ser a própria conta nem uma descendente dela.",
                    )

            account.update(
                nome=command.name, categoria_pai_id=command.parent_id, status=command.status,
                updated_by=command.actor.user_id, now=datetime.now(timezone.utc),
            )
            await repo.add(account)
            await uow.commit()

        return ChartOfAccountsDTO.from_entity(account)
