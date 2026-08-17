from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.expense_allocation import ExpenseAllocation
from modules.financial.domain.repositories.expense_allocation_repository import ExpenseAllocationRepository
from modules.financial.domain.value_objects.allocation_criterion import AllocationCriterion
from modules.financial.infrastructure.persistence.models.accounts_payable_model import ExpenseAllocationModel


def _to_entity(model: ExpenseAllocationModel) -> ExpenseAllocation:
    return ExpenseAllocation(
        id=model.id, conta_pagar_id=model.conta_pagar_id, centro_custo_id=model.centro_custo_id,
        viagem_id=model.viagem_id, criterio=AllocationCriterion(model.criterio), valor_rateado=model.valor_rateado,
    )


class SqlAlchemyExpenseAllocationRepository(ExpenseAllocationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[ExpenseAllocation]:
        tenant_id = get_current_tenant_id()
        stmt = select(ExpenseAllocationModel).where(
            ExpenseAllocationModel.tenant_id == tenant_id, ExpenseAllocationModel.conta_pagar_id == conta_pagar_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, allocation: ExpenseAllocation) -> None:
        tenant_id = get_current_tenant_id()
        model = ExpenseAllocationModel(
            id=allocation.id, tenant_id=tenant_id, conta_pagar_id=allocation.conta_pagar_id,
            centro_custo_id=allocation.centro_custo_id, viagem_id=allocation.viagem_id,
            criterio=allocation.criterio.value, valor_rateado=allocation.valor_rateado,
        )
        self._session.add(model)
        await self._session.flush()

    async def delete_for_payable(self, conta_pagar_id: uuid.UUID) -> None:
        tenant_id = get_current_tenant_id()
        await self._session.execute(
            delete(ExpenseAllocationModel).where(
                ExpenseAllocationModel.tenant_id == tenant_id, ExpenseAllocationModel.conta_pagar_id == conta_pagar_id
            )
        )
        await self._session.flush()

    async def sum_for_trip(self, viagem_id: uuid.UUID) -> Decimal:
        tenant_id = get_current_tenant_id()
        stmt = select(func.coalesce(func.sum(ExpenseAllocationModel.valor_rateado), 0)).where(
            ExpenseAllocationModel.tenant_id == tenant_id, ExpenseAllocationModel.viagem_id == viagem_id
        )
        total = (await self._session.execute(stmt)).scalar_one()
        return Decimal(total)
