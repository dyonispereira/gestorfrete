from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_anomaly_dto import AIAnomalyDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_anomaly_repository import (
    SqlAlchemyAIAnomalyRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetAnomalyQuery(Query):
    actor: AuthenticatedActor
    anomaly_id: uuid.UUID


class GetAnomalyHandler(QueryHandler[GetAnomalyQuery, AIAnomalyDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetAnomalyQuery) -> AIAnomalyDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIAnomalyRepository(session)
            anomaly = await repo.get_by_id(query.anomaly_id)
        if anomaly is None:
            raise NotFoundError("AI_ANOMALY_NOT_FOUND", "Anomalia Detectada não encontrada.")
        return AIAnomalyDTO.from_entity(anomaly)
