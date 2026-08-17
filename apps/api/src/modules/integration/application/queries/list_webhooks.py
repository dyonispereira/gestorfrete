from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.integration.application.dtos.webhook_dto import WebhookDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListWebhooksQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    integration_config_id: uuid.UUID | None
    status: str | None


@dataclass(frozen=True)
class ListWebhooksResult:
    items: list[WebhookDTO]
    total: int


class ListWebhooksHandler(QueryHandler[ListWebhooksQuery, ListWebhooksResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListWebhooksQuery) -> ListWebhooksResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyWebhookRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, integration_config_id=query.integration_config_id,
                status=query.status,
            )
            return ListWebhooksResult(items=[WebhookDTO.from_entity(w) for w in items], total=total)
