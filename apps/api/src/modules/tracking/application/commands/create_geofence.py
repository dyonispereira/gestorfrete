from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from modules.tracking.application.dtos.geofence_dto import GeofenceDTO
from modules.tracking.domain.entities.geofence import Geofence
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.geofence_geometry_type import GeofenceGeometryType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateGeofenceCommand(Command):
    actor: AuthenticatedActor
    name: str
    geometry_type: GeofenceGeometryType
    center: GeoPoint | None
    radius_meters: float | None
    polygon: list[GeoPoint] | None
    client_id: uuid.UUID | None
    branch_id: uuid.UUID | None


class CreateGeofenceHandler(CommandHandler[CreateGeofenceCommand, GeofenceDTO]):
    """`branch_id` nunca é validado contra um repositório — `Filial` ainda não tem tabela física
    (D403); a checagem `404` de `052-geofences.md` se aplica só a `client_id` nesta fundação."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateGeofenceCommand) -> GeofenceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyGeofenceRepository(uow.session)
            client_repo = SqlAlchemyClientRepository(uow.session)

            if await repo.get_by_nome(command.name) is not None:
                raise ConflictError("TRACKING_GEOFENCE_NAME_ALREADY_EXISTS", "Já existe uma cerca com esse nome.")
            if command.client_id is not None and await client_repo.get_by_id(command.client_id) is None:
                raise NotFoundError("TRACKING_GEOFENCE_CLIENT_NOT_FOUND", "Cliente não encontrado.")

            geofence = Geofence.create(
                nome=command.name, tipo_geometria=command.geometry_type, centro=command.center,
                raio_metros=command.radius_meters, poligono=command.polygon, cliente_id=command.client_id,
                filial_id=command.branch_id,
            )
            await repo.add(geofence)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cercas_eletronicas",
                entidade_id=geofence.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"nome": geofence.nome},
            )
            await uow.commit()

        return GeofenceDTO.from_entity(geofence)
