from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.tracking.application.dtos.speed_limit_config_dto import SpeedLimitConfigDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_speed_limit_config_repository import (
    SqlAlchemySpeedLimitConfigRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSpeedLimitConfigsQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    vehicle_category_id: uuid.UUID | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListSpeedLimitConfigsResult:
    items: list[SpeedLimitConfigDTO]
    total: int


class ListSpeedLimitConfigsHandler(QueryHandler[ListSpeedLimitConfigsQuery, ListSpeedLimitConfigsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSpeedLimitConfigsQuery) -> ListSpeedLimitConfigsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemySpeedLimitConfigRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, vehicle_category_id=query.vehicle_category_id,
                status=query.status,
            )
        return ListSpeedLimitConfigsResult(items=[SpeedLimitConfigDTO.from_entity(c) for c in items], total=total)
