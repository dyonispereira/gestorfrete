from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.financial_reversal import FinancialReversal
from modules.financial.domain.repositories.financial_reversal_repository import FinancialReversalRepository
from modules.financial.infrastructure.persistence.models.financial_reversal_model import FinancialReversalModel


def _to_entity(model: FinancialReversalModel) -> FinancialReversal:
    return FinancialReversal(
        id=model.id, fatura_id=model.fatura_id, conta_pagar_id=model.conta_pagar_id,
        conta_receber_id=model.conta_receber_id, valor=model.valor, motivo=model.motivo, data_hora=model.data_hora,
    )


class SqlAlchemyFinancialReversalRepository(FinancialReversalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> FinancialReversal | None:
        tenant_id = get_current_tenant_id()
        stmt = select(FinancialReversalModel).where(
            FinancialReversalModel.id == id, FinancialReversalModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, reversal: FinancialReversal) -> None:
        tenant_id = get_current_tenant_id()
        model = FinancialReversalModel(
            id=reversal.id, tenant_id=tenant_id, fatura_id=reversal.fatura_id,
            conta_pagar_id=reversal.conta_pagar_id, conta_receber_id=reversal.conta_receber_id,
            valor=reversal.valor, motivo=reversal.motivo, data_hora=reversal.data_hora,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        invoice_id: uuid.UUID | None,
        accounts_payable_id: uuid.UUID | None,
        accounts_receivable_id: uuid.UUID | None,
    ) -> tuple[list[FinancialReversal], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(FinancialReversalModel).where(FinancialReversalModel.tenant_id == tenant_id)
        if invoice_id is not None:
            stmt = stmt.where(FinancialReversalModel.fatura_id == invoice_id)
        if accounts_payable_id is not None:
            stmt = stmt.where(FinancialReversalModel.conta_pagar_id == accounts_payable_id)
        if accounts_receivable_id is not None:
            stmt = stmt.where(FinancialReversalModel.conta_receber_id == accounts_receivable_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(FinancialReversalModel.data_hora.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total
