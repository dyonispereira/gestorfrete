from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.dtos.invoice_dto import InvoiceDTO, InvoiceTripDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_trip_repository import (
    SqlAlchemyInvoiceTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListInvoicesQuery(Query):
    actor: AuthenticatedActor
    page: int = 1
    limit: int = 20
    client_id: uuid.UUID | None = None
    status: str | None = None
    trip_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ListInvoicesResult:
    items: list[InvoiceDTO]
    total: int


class ListInvoicesHandler(QueryHandler[ListInvoicesQuery, ListInvoicesResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListInvoicesQuery) -> ListInvoicesResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyInvoiceRepository(session)
            invoices, total = await repo.list_page(
                page=query.page, limit=query.limit, client_id=query.client_id,
                status=query.status, trip_id=query.trip_id,
            )
            trips_by_invoice = await SqlAlchemyInvoiceTripRepository(session).list_for_invoices_batch(
                [i.id for i in invoices]
            )
        return ListInvoicesResult(
            items=[
                InvoiceDTO.from_entity(i, trips=[InvoiceTripDTO.from_entity(t) for t in trips_by_invoice.get(i.id, [])])
                for i in invoices
            ],
            total=total,
        )
