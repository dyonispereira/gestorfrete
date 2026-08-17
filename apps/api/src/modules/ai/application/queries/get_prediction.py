from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_prediction_dto import AIPredictionDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_prediction_repository import (
    SqlAlchemyAIPredictionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetPredictionQuery(Query):
    actor: AuthenticatedActor
    prediction_id: uuid.UUID


class GetPredictionHandler(QueryHandler[GetPredictionQuery, AIPredictionDTO]):
    """D312/D425 — `status` sempre recalculado contra `now()`, nunca confiado cegamente ao valor
    físico gravado."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetPredictionQuery) -> AIPredictionDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIPredictionRepository(session)
            prediction = await repo.get_by_id(query.prediction_id)
        if prediction is None:
            raise NotFoundError("AI_PREDICTION_NOT_FOUND", "Predição de IA não encontrada.")
        return AIPredictionDTO.from_entity(prediction, now=datetime.now(timezone.utc))
