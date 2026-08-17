from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.fiscal_event_dto import FiscalEventDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_event_repository import (
    SqlAlchemyFiscalEventRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetFiscalEventQuery(Query):
    actor: AuthenticatedActor
    fiscal_event_id: uuid.UUID


class GetFiscalEventHandler(QueryHandler[GetFiscalEventQuery, FiscalEventDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetFiscalEventQuery) -> FiscalEventDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyFiscalEventRepository(session)
            event = await repo.get_by_id(query.fiscal_event_id)
        if event is None:
            raise NotFoundError("FISCAL_EVENT_NOT_FOUND", "Evento Fiscal não encontrado.")
        return FiscalEventDTO.from_entity(event)
