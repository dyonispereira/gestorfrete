from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.tracking_equipment_dto import TrackingEquipmentDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_equipment_repository import (
    SqlAlchemyTrackingEquipmentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTrackingEquipmentQuery(Query):
    actor: AuthenticatedActor
    equipment_id: uuid.UUID


class GetTrackingEquipmentHandler(QueryHandler[GetTrackingEquipmentQuery, TrackingEquipmentDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTrackingEquipmentQuery) -> TrackingEquipmentDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingEquipmentRepository(session)
            equipment = await repo.get_by_id(query.equipment_id)
        if equipment is None:
            raise NotFoundError("TRACKING_EQUIPMENT_NOT_FOUND", "Equipamento de Rastreamento não encontrado.")
        return TrackingEquipmentDTO.from_entity(equipment)
