from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.geofence_dto import GeofenceDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetGeofenceQuery(Query):
    actor: AuthenticatedActor
    geofence_id: uuid.UUID


class GetGeofenceHandler(QueryHandler[GetGeofenceQuery, GeofenceDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetGeofenceQuery) -> GeofenceDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyGeofenceRepository(session)
            geofence = await repo.get_by_id(query.geofence_id)
        if geofence is None:
            raise NotFoundError("TRACKING_GEOFENCE_NOT_FOUND", "Cerca Eletrônica não encontrada.")
        return GeofenceDTO.from_entity(geofence)
