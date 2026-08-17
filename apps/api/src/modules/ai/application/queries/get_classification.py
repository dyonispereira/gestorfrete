from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_classification_dto import AIClassificationDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_classification_repository import (
    SqlAlchemyAIClassificationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetClassificationQuery(Query):
    actor: AuthenticatedActor
    classification_id: uuid.UUID


class GetClassificationHandler(QueryHandler[GetClassificationQuery, AIClassificationDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetClassificationQuery) -> AIClassificationDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIClassificationRepository(session)
            classification = await repo.get_by_id(query.classification_id)
        if classification is None:
            raise NotFoundError("AI_CLASSIFICATION_NOT_FOUND", "Classificação de IA não encontrada.")
        return AIClassificationDTO.from_entity(classification)
