from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.tracking_provider_dto import TrackingProviderDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_provider_repository import (
    SqlAlchemyTrackingProviderRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTrackingProviderQuery(Query):
    actor: AuthenticatedActor
    provider_id: uuid.UUID


class GetTrackingProviderHandler(QueryHandler[GetTrackingProviderQuery, TrackingProviderDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTrackingProviderQuery) -> TrackingProviderDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingProviderRepository(session)
            provider = await repo.get_by_id(query.provider_id)
        if provider is None:
            raise NotFoundError("TRACKING_PROVIDER_NOT_FOUND", "Provedor de Rastreamento não encontrado.")
        return TrackingProviderDTO.from_entity(provider)
