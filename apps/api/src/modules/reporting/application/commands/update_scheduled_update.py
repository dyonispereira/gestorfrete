from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.reporting.application.dtos.scheduled_update_dto import ScheduledUpdateDTO
from modules.reporting.domain.value_objects.scheduled_update_mode import ScheduledUpdateMode
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_scheduled_update_repository import (
    SqlAlchemyScheduledUpdateRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateScheduledUpdateCommand(Command):
    actor: AuthenticatedActor
    scheduled_update_id: uuid.UUID
    mode: ScheduledUpdateMode | None
    status: str | None


class UpdateScheduledUpdateHandler(CommandHandler[UpdateScheduledUpdateCommand, ScheduledUpdateDTO]):
    """`070` — alvo (`metric_id`/`cube_id`) não é editável; trocar o alvo é criar um novo."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateScheduledUpdateCommand) -> ScheduledUpdateDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyScheduledUpdateRepository(uow.session)
            scheduled_update = await repo.get_by_id(command.scheduled_update_id)
            if scheduled_update is None:
                raise NotFoundError("REPORTING_SCHEDULED_UPDATE_NOT_FOUND", "Agendamento não encontrado.")

            scheduled_update.update(modo=command.mode, status=command.status)
            await repo.add(scheduled_update)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="agendamentos_atualizacao",
                entidade_id=scheduled_update.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return ScheduledUpdateDTO.from_entity(scheduled_update)
