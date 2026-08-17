from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.reporting.application.dtos.scheduled_update_dto import ScheduledUpdateDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_scheduled_update_repository import (
    SqlAlchemyScheduledUpdateRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetScheduledUpdateQuery(Query):
    actor: AuthenticatedActor
    scheduled_update_id: uuid.UUID


class GetScheduledUpdateHandler(QueryHandler[GetScheduledUpdateQuery, ScheduledUpdateDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetScheduledUpdateQuery) -> ScheduledUpdateDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyScheduledUpdateRepository(session)
            scheduled_update = await repo.get_by_id(query.scheduled_update_id)
        if scheduled_update is None:
            raise NotFoundError("REPORTING_SCHEDULED_UPDATE_NOT_FOUND", "Agendamento não encontrado.")
        return ScheduledUpdateDTO.from_entity(scheduled_update)
