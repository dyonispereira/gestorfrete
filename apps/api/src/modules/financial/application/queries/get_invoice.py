from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.invoice_dto import InvoiceDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
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
            repo = SqlAlchemyInvoiceRepository(session)
            invoice = await repo.get_by_id(query.invoice_id)
        if invoice is None:
            raise NotFoundError("FINANCIAL_INVOICE_NOT_FOUND", "Fatura não encontrada.")
        return InvoiceDTO.from_entity(invoice)
