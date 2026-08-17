from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai.application.dtos.ai_prediction_dto import AIPredictionDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_prediction_repository import (
    SqlAlchemyAIPredictionRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListPredictionsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    category: str | None
    target_entity_type: str | None
    target_entity_id: uuid.UUID | None
    include_expired: bool


@dataclass(frozen=True)
class ListPredictionsResult:
    items: list[AIPredictionDTO]
    total: int


class ListPredictionsHandler(QueryHandler[ListPredictionsQuery, ListPredictionsResult]):
    """`074`/D312 — `include_expired=False` (padrão) só lista predições cujo status EFETIVO é
    `ATUAL`; nunca omite silenciosamente uma predição vencida quando `include_expired=True`."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListPredictionsQuery) -> ListPredictionsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyAIPredictionRepository(session)
            items, total = await repo.list_page(
                page=query.page, limit=query.limit, categoria=query.category,
                entidade_alvo_tipo=query.target_entity_type, entidade_alvo_id=query.target_entity_id,
                include_expired=query.include_expired,
            )
            now = datetime.now(timezone.utc)
            return ListPredictionsResult(
                items=[AIPredictionDTO.from_entity(p, now=now) for p in items], total=total
            )
