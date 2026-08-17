from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.expense_approval import ExpenseApproval
from modules.financial.domain.repositories.expense_approval_repository import ExpenseApprovalRepository
from modules.financial.domain.value_objects.expense_approval_decision import ExpenseApprovalDecision
from modules.financial.infrastructure.persistence.models.accounts_payable_model import ExpenseApprovalModel


def _to_entity(model: ExpenseApprovalModel) -> ExpenseApproval:
    return ExpenseApproval(
        id=model.id, conta_pagar_id=model.conta_pagar_id, decisao=ExpenseApprovalDecision(model.decisao),
        justificativa=model.justificativa, ator_id=model.ator_id, data_hora=model.data_hora,
    )


class SqlAlchemyExpenseApprovalRepository(ExpenseApprovalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_payable(self, conta_pagar_id: uuid.UUID) -> list[ExpenseApproval]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(ExpenseApprovalModel)
            .where(ExpenseApprovalModel.tenant_id == tenant_id, ExpenseApprovalModel.conta_pagar_id == conta_pagar_id)
            .order_by(ExpenseApprovalModel.data_hora)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, approval: ExpenseApproval) -> None:
        tenant_id = get_current_tenant_id()
        model = ExpenseApprovalModel(
            id=approval.id, tenant_id=tenant_id, conta_pagar_id=approval.conta_pagar_id,
            decisao=approval.decisao.value, justificativa=approval.justificativa, ator_id=approval.ator_id,
            data_hora=approval.data_hora,
        )
        self._session.add(model)
        await self._session.flush()
