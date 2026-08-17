from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.tracking.application.dtos.tracking_equipment_dto import TrackingEquipmentDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_equipment_repository import (
    SqlAlchemyTrackingEquipmentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTrackingEquipmentQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    vehicle_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    equipment_type: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListTrackingEquipmentResult:
    items: list[TrackingEquipmentDTO]
    total: int


class ListTrackingEquipmentHandler(QueryHandler[ListTrackingEquipmentQuery, ListTrackingEquipmentResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTrackingEquipmentQuery) -> ListTrackingEquipmentResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingEquipmentRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, vehicle_id=query.vehicle_id, provider_id=query.provider_id,
                equipment_type=query.equipment_type, status=query.status,
            )
        return ListTrackingEquipmentResult(items=[TrackingEquipmentDTO.from_entity(e) for e in items], total=total)
