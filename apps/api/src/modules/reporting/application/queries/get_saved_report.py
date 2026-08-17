from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.saved_report_dto import SavedReportDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_report_repository import (
    SqlAlchemySavedReportRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSavedReportQuery(Query):
    actor: AuthenticatedActor
    saved_report_id: uuid.UUID


class GetSavedReportHandler(QueryHandler[GetSavedReportQuery, SavedReportDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSavedReportQuery) -> SavedReportDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemySavedReportRepository(session)
            saved_report = await repo.get_by_id(query.saved_report_id)
        if saved_report is None:
            raise NotFoundError("REPORTING_SAVED_REPORT_NOT_FOUND", "Relatório Salvo não encontrado.")
        if saved_report.usuario_id != query.actor.user_id:
            raise AuthorizationError("REPORTING_SAVED_REPORT_FORBIDDEN", "Relatório Salvo não pertence ao usuário.")
        return SavedReportDTO.from_entity(saved_report)
