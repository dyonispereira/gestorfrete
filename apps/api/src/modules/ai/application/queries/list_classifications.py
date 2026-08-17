from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_classification_dto import AIClassificationDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_classification_repository import (
    SqlAlchemyAIClassificationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListClassificationsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    classification_type: str | None
    target_entity_type: str | None
    target_entity_id: uuid.UUID | None


@dataclass(frozen=True)
class ListClassificationsResult:
    items: list[AIClassificationDTO]
    total: int


class ListClassificationsHandler(QueryHandler[ListClassificationsQuery, ListClassificationsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListClassificationsQuery) -> ListClassificationsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIClassificationRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, tipo_classificacao=query.classification_type,
                entidade_alvo_tipo=query.target_entity_type, entidade_alvo_id=query.target_entity_id,
            )
            return ListClassificationsResult(items=[AIClassificationDTO.from_entity(c) for c in items], total=total)
