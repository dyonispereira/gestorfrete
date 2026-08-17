from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.vehicle_document_dto import VehicleDocumentDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_document_repository import (
    SqlAlchemyVehicleDocumentRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListVehicleDocumentsQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    page: int = 1
    limit: int = 20
    tipo: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ListVehicleDocumentsResult:
    items: list[VehicleDocumentDTO]
    total: int


class ListVehicleDocumentsHandler(QueryHandler[ListVehicleDocumentsQuery, ListVehicleDocumentsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehicleDocumentsQuery) -> ListVehicleDocumentsResult:
        async with self._session_factory() as session:
            vehicle_repo = SqlAlchemyVehicleRepository(session)
            if await vehicle_repo.get_by_id(query.vehicle_id) is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            doc_repo = SqlAlchemyVehicleDocumentRepository(session)
            documents, total = await doc_repo.list_page(
                veiculo_tracionador_id=query.vehicle_id, page=query.page, limit=query.limit, tipo=query.tipo, status=query.status
            )
        return ListVehicleDocumentsResult(items=[VehicleDocumentDTO.from_entity(d) for d in documents], total=total)
