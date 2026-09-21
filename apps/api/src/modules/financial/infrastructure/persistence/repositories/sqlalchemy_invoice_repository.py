from __future__ import annotations

import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.invoice import Invoice
from modules.financial.domain.repositories.invoice_repository import InvoiceRepository
from modules.financial.domain.value_objects.invoice_status import InvoiceStatus
from modules.financial.infrastructure.persistence.models.invoice_model import InvoiceModel, InvoiceTripModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: InvoiceModel) -> Invoice:
    return Invoice(
        id=model.id, numero_fatura=model.numero_fatura, entrega_id=model.entrega_id,
        cliente_id=model.cliente_id, valor_bruto=model.valor_bruto, valor_ajuste=model.valor_ajuste,
        motivo_ajuste=model.motivo_ajuste, valor_total=model.valor_total, data_emissao=model.data_emissao,
        forma_pagamento_id=model.forma_pagamento_id, status=InvoiceStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em, created_by=model.criado_por, updated_at=model.atualizado_em,
            updated_by=model.atualizado_por, deleted_at=model.excluido_em, deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyInvoiceRepository(InvoiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Invoice | None:
        tenant_id = get_current_tenant_id()
        stmt = select(InvoiceModel).where(InvoiceModel.id == id, InvoiceModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_numero(self, numero_fatura: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(InvoiceModel.id).where(InvoiceModel.tenant_id == tenant_id, InvoiceModel.numero_fatura == numero_fatura)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, client_id: uuid.UUID | None, status: str | None, trip_id: uuid.UUID | None
    ) -> tuple[list[Invoice], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id)
        if client_id is not None:
            stmt = stmt.where(InvoiceModel.cliente_id == client_id)
        if status is not None:
            stmt = stmt.where(InvoiceModel.status == status)
        if trip_id is not None:
            # Reconciliado (Lote Financeiro, Parte 3) — `faturas` não tem mais `viagem_id` direto;
            # o filtro passa a ser EXISTS contra `fatura_viagens`.
            stmt = stmt.where(
                exists().where(InvoiceTripModel.fatura_id == InvoiceModel.id, InvoiceTripModel.viagem_id == trip_id)
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(InvoiceModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Invoice) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(InvoiceModel, aggregate.id)
        if model is None:
            model = InvoiceModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.numero_fatura = aggregate.numero_fatura
        model.entrega_id = aggregate.entrega_id
        model.cliente_id = aggregate.cliente_id
        model.valor_bruto = aggregate.valor_bruto
        model.valor_ajuste = aggregate.valor_ajuste
        model.motivo_ajuste = aggregate.motivo_ajuste
        model.valor_total = aggregate.valor_total
        model.data_emissao = aggregate.data_emissao
        model.forma_pagamento_id = aggregate.forma_pagamento_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Invoice]) -> list[Invoice]:
        raise NotImplementedError("Use list_page — filtros de Invoice são resolvidos via SQL")
