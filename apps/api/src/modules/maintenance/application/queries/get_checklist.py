from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetChecklistQuery(Query):
    actor: AuthenticatedActor
    checklist_id: uuid.UUID


class GetChecklistHandler(QueryHandler[GetChecklistQuery, ChecklistDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetChecklistQuery) -> ChecklistDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyChecklistRepository(session)
            checklist = await repo.get_by_id(query.checklist_id)
        if checklist is None:
            raise NotFoundError("MAINTENANCE_CHECKLIST_NOT_FOUND", "Checklist não encontrado.")
        return ChecklistDTO.from_entity(checklist)
