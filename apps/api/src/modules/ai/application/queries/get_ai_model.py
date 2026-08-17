from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_model_dto import AIModelDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAIModelQuery(Query):
    actor: AuthenticatedActor
    model_id: uuid.UUID


class GetAIModelHandler(QueryHandler[GetAIModelQuery, AIModelDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAIModelQuery) -> AIModelDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIModelRepository(session)
            model = await repo.get_by_id(query.model_id)
        if model is None:
            raise NotFoundError("AI_MODEL_NOT_FOUND", "Modelo de IA não encontrado.")
        return AIModelDTO.from_entity(model)
