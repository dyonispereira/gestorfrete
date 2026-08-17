from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.integration.application.dtos.integration_config_dto import IntegrationConfigDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_integration_config_repository import (
    SqlAlchemyIntegrationConfigRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListIntegrationConfigsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    type: str | None
    status: str | None


@dataclass(frozen=True)
class ListIntegrationConfigsResult:
    items: list[IntegrationConfigDTO]
    total: int


class ListIntegrationConfigsHandler(QueryHandler[ListIntegrationConfigsQuery, ListIntegrationConfigsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListIntegrationConfigsQuery) -> ListIntegrationConfigsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyIntegrationConfigRepository(session)
            items, total = await repo.list_page(page=query.page, limit=query.limit, tipo=query.type, status=query.status)
            return ListIntegrationConfigsResult(items=[IntegrationConfigDTO.from_entity(c) for c in items], total=total)
