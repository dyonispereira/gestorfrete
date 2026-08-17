from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.tracking.application.dtos.tracking_provider_dto import TrackingProviderDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_provider_repository import (
    SqlAlchemyTrackingProviderRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTrackingProvidersQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    search: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListTrackingProvidersResult:
    items: list[TrackingProviderDTO]
    total: int


class ListTrackingProvidersHandler(QueryHandler[ListTrackingProvidersQuery, ListTrackingProvidersResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTrackingProvidersQuery) -> ListTrackingProvidersResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyTrackingProviderRepository(session)
            providers, total = await repo.list_page(
                page=query.page, limit=query.limit, search=query.search, status=query.status
            )
        return ListTrackingProvidersResult(items=[TrackingProviderDTO.from_entity(p) for p in providers], total=total)
