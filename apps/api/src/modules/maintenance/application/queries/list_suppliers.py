from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.maintenance.application.dtos.supplier_dto import SupplierDTO
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListSuppliersQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    status: str | None = None
    category: str | None = None
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


@dataclass(frozen=True)
class ListSuppliersResult:
    items: list[SupplierDTO]
    total: int


class ListSuppliersHandler(QueryHandler[ListSuppliersQuery, ListSuppliersResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListSuppliersQuery) -> ListSuppliersResult:
        async with self._session_factory() as session:
            repo = SqlAlchemySupplierRepository(session)
            suppliers, total = await repo.list_page(
                page=query.page,
                limit=query.limit,
                status=query.status,
                category=query.category,
                search=query.search,
                created_from=query.created_from,
                created_to=query.created_to,
            )
        return ListSuppliersResult(items=[SupplierDTO.from_entity(s) for s in suppliers], total=total)
