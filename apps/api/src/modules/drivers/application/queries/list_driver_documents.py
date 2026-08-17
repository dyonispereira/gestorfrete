from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.drivers.application.dtos.driver_document_dto import DriverDocumentDTO
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_document_repository import (
    SqlAlchemyDriverDocumentRepository,
)
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListDriverDocumentsQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID


class ListDriverDocumentsHandler(QueryHandler[ListDriverDocumentsQuery, list[DriverDocumentDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListDriverDocumentsQuery) -> list[DriverDocumentDTO]:
        async with self._session_factory() as session:
            driver_repo = SqlAlchemyDriverRepository(session)
            if await driver_repo.get_by_id(query.driver_id) is None:
                raise NotFoundError("DRIVERS_DRIVER_NOT_FOUND", "Motorista não encontrado.")

            doc_repo = SqlAlchemyDriverDocumentRepository(session)
            documents = await doc_repo.list_for_driver(query.driver_id)
        return [DriverDocumentDTO.from_entity(d) for d in documents]
