from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.tracking.application.dtos.tracking_event_dto import TrackingEventDTO
from modules.tracking.application.queries.tracking_event_permission_map import EVENT_TYPE_PERMISSION
from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_event_repository import (
    SqlAlchemyTrackingEventRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTrackingEventQuery(Query):
    actor: AuthenticatedActor
    event_id: uuid.UUID


class GetTrackingEventHandler(QueryHandler[GetTrackingEventQuery, TrackingEventDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._authz = AuthorizationService(session_factory)

    async def handle(self, query: GetTrackingEventQuery) -> TrackingEventDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingEventRepository(session)
            event = await repo.get_by_id(query.event_id)
        if event is None:
            raise NotFoundError("TRACKING_EVENT_NOT_FOUND", "Evento de Rastreamento não encontrado.")

        required = EVENT_TYPE_PERMISSION[TrackingEventType(event.tipo)]
        granted_codes = await self._authz.get_permission_codes(query.actor)
        if required not in granted_codes:
            raise AuthorizationError("IDENTITY_PERMISSION_DENIED", f"Ação requer a permissão '{required}'.")

        return TrackingEventDTO.from_entity(event)
