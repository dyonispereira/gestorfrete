from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.invoice_trip import InvoiceTrip
from modules.financial.domain.repositories.invoice_trip_repository import InvoiceTripRepository
from modules.financial.domain.value_objects.invoice_status import InvoiceStatus
from modules.financial.infrastructure.persistence.models.invoice_model import InvoiceModel, InvoiceTripModel


def _to_entity(model: InvoiceTripModel) -> InvoiceTrip:
    return InvoiceTrip(id=model.id, fatura_id=model.fatura_id, viagem_id=model.viagem_id, valor=model.valor, criado_em=model.criado_em)


class SqlAlchemyInvoiceTripRepository(InvoiceTripRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invoice_trip: InvoiceTrip) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(InvoiceTripModel, invoice_trip.id)
        if model is None:
            model = InvoiceTripModel(id=invoice_trip.id, tenant_id=tenant_id)
            self._session.add(model)
        model.fatura_id = invoice_trip.fatura_id
        model.viagem_id = invoice_trip.viagem_id
        model.valor = invoice_trip.valor
        model.criado_em = invoice_trip.criado_em
        await self._session.flush()

    async def list_for_invoice(self, fatura_id: uuid.UUID) -> list[InvoiceTrip]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(InvoiceTripModel)
            .where(InvoiceTripModel.tenant_id == tenant_id, InvoiceTripModel.fatura_id == fatura_id)
            .order_by(InvoiceTripModel.criado_em.asc())
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def list_for_invoices_batch(self, fatura_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[InvoiceTrip]]:
        if not fatura_ids:
            return {}
        tenant_id = get_current_tenant_id()
        stmt = (
            select(InvoiceTripModel)
            .where(InvoiceTripModel.tenant_id == tenant_id, InvoiceTripModel.fatura_id.in_(fatura_ids))
            .order_by(InvoiceTripModel.criado_em.asc())
        )
        models = (await self._session.execute(stmt)).scalars().all()
        result: dict[uuid.UUID, list[InvoiceTrip]] = {}
        for model in models:
            result.setdefault(model.fatura_id, []).append(_to_entity(model))
        return result

    async def exists_active_for_trip(self, viagem_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(InvoiceTripModel.id)
            .join(InvoiceModel, InvoiceModel.id == InvoiceTripModel.fatura_id)
            .where(
                InvoiceTripModel.tenant_id == tenant_id, InvoiceTripModel.viagem_id == viagem_id,
                InvoiceModel.status != InvoiceStatus.CANCELADA.value,
            )
        )
        return (await self._session.execute(stmt)).first() is not None
