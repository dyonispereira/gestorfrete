from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.tracking.application.dtos.geofence_dto import GeofenceDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListGeofencesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None
    geometry_type: str | None = None
    client_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListGeofencesResult:
    items: list[GeofenceDTO]
    total: int


class ListGeofencesHandler(QueryHandler[ListGeofencesQuery, ListGeofencesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListGeofencesQuery) -> ListGeofencesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyGeofenceRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, geometry_type=query.geometry_type,
                client_id=query.client_id, branch_id=query.branch_id, status=query.status,
            )
        return ListGeofencesResult(items=[GeofenceDTO.from_entity(g) for g in items], total=total)
