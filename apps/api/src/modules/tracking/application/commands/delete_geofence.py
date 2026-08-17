from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteGeofenceCommand(Command):
    actor: AuthenticatedActor
    geofence_id: uuid.UUID


class DeleteGeofenceHandler(CommandHandler[DeleteGeofenceCommand, None]):
    """D219 — soft delete (`status=INATIVA`), nunca `DELETE FROM`. `TRACKING_GEOFENCE_IN_USE` (422)
    quando `eventos_rastreamento` recentes referenciam esta cerca (D001 — histórico nunca quebra)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteGeofenceCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyGeofenceRepository(uow.session)
            geofence = await repo.get_by_id(command.geofence_id)
            if geofence is None:
                raise NotFoundError("TRACKING_GEOFENCE_NOT_FOUND", "Cerca Eletrônica não encontrada.")
            if await repo.is_referenced_by_recent_events(geofence.id):
                raise DomainError(
                    "TRACKING_GEOFENCE_IN_USE", "Cerca referenciada por eventos de rastreamento recentes."
                )

            await repo.delete(geofence)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cercas_eletronicas",
                entidade_id=geofence.id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
