from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.saved_filter_dto import SavedFilterDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_filter_repository import (
    SqlAlchemySavedFilterRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSavedFilterQuery(Query):
    actor: AuthenticatedActor
    saved_filter_id: uuid.UUID


class GetSavedFilterHandler(QueryHandler[GetSavedFilterQuery, SavedFilterDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSavedFilterQuery) -> SavedFilterDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemySavedFilterRepository(session)
            saved_filter = await repo.get_by_id(query.saved_filter_id)
        if saved_filter is None:
            raise NotFoundError("REPORTING_SAVED_FILTER_NOT_FOUND", "Filtro Favorito não encontrado.")
        if saved_filter.usuario_id != query.actor.user_id:
            raise AuthorizationError("REPORTING_SAVED_FILTER_FORBIDDEN", "Filtro Favorito não pertence ao usuário.")
        return SavedFilterDTO.from_entity(saved_filter)
