from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.webhook_dto import WebhookDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetWebhookQuery(Query):
    actor: AuthenticatedActor
    webhook_id: uuid.UUID


class GetWebhookHandler(QueryHandler[GetWebhookQuery, WebhookDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetWebhookQuery) -> WebhookDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyWebhookRepository(session)
            webhook = await repo.get_by_id(query.webhook_id)
        if webhook is None:
            raise NotFoundError("INTEGRATION_WEBHOOK_NOT_FOUND", "Webhook não encontrado.")
        return WebhookDTO.from_entity(webhook)
