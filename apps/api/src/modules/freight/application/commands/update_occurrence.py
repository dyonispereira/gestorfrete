from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_status import OccurrenceStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_occurrence_repository import (
    SqlAlchemyOccurrenceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateOccurrenceCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    occurrence_id: uuid.UUID
    descricao: str | None
    gravidade: OccurrenceSeverity | None
    status: OccurrenceStatus | None


class UpdateOccurrenceHandler(CommandHandler[UpdateOccurrenceCommand, OccurrenceDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateOccurrenceCommand) -> OccurrenceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            occurrence_repo = SqlAlchemyOccurrenceRepository(uow.session)

            occurrence = await occurrence_repo.get_by_id(command.occurrence_id)
            if occurrence is None or occurrence.viagem_id != command.trip_id:
                raise NotFoundError("FREIGHT_OCCURRENCE_NOT_FOUND", "Ocorrência não encontrada.")

            occurrence.update(descricao=command.descricao, gravidade=command.gravidade, status=command.status)
            await occurrence_repo.add(occurrence)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="ocorrencias",
                entidade_id=occurrence.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": occurrence.status.value},
            )

            await uow.commit()

        return OccurrenceDTO.from_entity(occurrence)
