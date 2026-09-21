from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
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
class GetInvoiceQuery(Query):
    actor: AuthenticatedActor
    invoice_id: uuid.UUID


class GetInvoiceHandler(QueryHandler[GetInvoiceQuery, InvoiceDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetInvoiceQuery) -> InvoiceDTO:
        async with self._session_factory() as session:
            invoice = await SqlAlchemyInvoiceRepository(session).get_by_id(query.invoice_id)
            if invoice is None:
                raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")
            trips = await SqlAlchemyInvoiceTripRepository(session).list_for_invoice(query.invoice_id)
        return InvoiceDTO.from_entity(invoice, trips=[InvoiceTripDTO.from_entity(t) for t in trips])
