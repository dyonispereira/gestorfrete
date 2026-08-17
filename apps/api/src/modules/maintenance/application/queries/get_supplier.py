from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.supplier_dto import SupplierDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSupplierQuery(Query):
    actor: AuthenticatedActor
    supplier_id: uuid.UUID


class GetSupplierHandler(QueryHandler[GetSupplierQuery, SupplierDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSupplierQuery) -> SupplierDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemySupplierRepository(session)
            supplier = await repo.get_by_id(query.supplier_id)
        if supplier is None:
            raise NotFoundError("MAINTENANCE_SUPPLIER_NOT_FOUND", "Fornecedor não encontrado.")
        return SupplierDTO.from_entity(supplier)
