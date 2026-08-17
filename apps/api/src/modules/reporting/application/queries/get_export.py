from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.export_dto import ExportDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_export_repository import (
    SqlAlchemyExportRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetExportQuery(Query):
    actor: AuthenticatedActor
    export_id: uuid.UUID


class GetExportHandler(QueryHandler[GetExportQuery, ExportDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetExportQuery) -> ExportDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyExportRepository(session)
            export = await repo.get_by_id(query.export_id)
        if export is None:
            raise NotFoundError("REPORTING_EXPORT_NOT_FOUND", "Exportação não encontrada.")
        if export.usuario_id != query.actor.user_id:
            raise AuthorizationError("REPORTING_EXPORT_FORBIDDEN", "Exportação não pertence ao usuário.")
        return ExportDTO.from_entity(export)
