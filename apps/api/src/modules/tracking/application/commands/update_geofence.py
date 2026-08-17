from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.geofence_dto import GeofenceDTO
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.geofence_geometry_type import GeofenceGeometryType
from modules.tracking.domain.value_objects.geofence_status import GeofenceStatus
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateGeofenceCommand(Command):
    actor: AuthenticatedActor
    geofence_id: uuid.UUID
    name: str | None
    geometry_type: GeofenceGeometryType | None
    center: GeoPoint | None
    radius_meters: float | None
    polygon: list[GeoPoint] | None
    client_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    status: GeofenceStatus | None


class UpdateGeofenceHandler(CommandHandler[UpdateGeofenceCommand, GeofenceDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateGeofenceCommand) -> GeofenceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyGeofenceRepository(uow.session)
            geofence = await repo.get_by_id(command.geofence_id)
            if geofence is None:
                raise NotFoundError("TRACKING_GEOFENCE_NOT_FOUND", "Cerca Eletrônica não encontrada.")

            geofence.update(
                nome=command.name, tipo_geometria=command.geometry_type, centro=command.center,
                raio_metros=command.radius_meters, poligono=command.polygon, cliente_id=command.client_id,
                filial_id=command.branch_id, status=command.status,
            )
            await repo.add(geofence)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cercas_eletronicas",
                entidade_id=geofence.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return GeofenceDTO.from_entity(geofence)
