from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_document_dto import DriverDocumentDTO
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_document_repository import (
    SqlAlchemyDriverDocumentRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetDriverDocumentQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    document_id: uuid.UUID


class GetDriverDocumentHandler(QueryHandler[GetDriverDocumentQuery, DriverDocumentDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetDriverDocumentQuery) -> DriverDocumentDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDriverDocumentRepository(session)
            document = await repo.get_by_id(query.document_id)
        if document is None or document.motorista_id != query.driver_id:
            raise NotFoundError("DRIVERS_DOCUMENT_NOT_FOUND", "Documento não encontrado.")
        return DriverDocumentDTO.from_entity(document)
