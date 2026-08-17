from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.accounts_receivable import AccountsReceivable
from modules.financial.domain.repositories.accounts_receivable_repository import AccountsReceivableRepository
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.models.accounts_receivable_model import AccountsReceivableModel


def _to_entity(model: AccountsReceivableModel) -> AccountsReceivable:
    return AccountsReceivable(
        id=model.id, fatura_id=model.fatura_id, numero_parcela=model.numero_parcela, valor=model.valor,
        data_vencimento=model.data_vencimento, data_recebimento=model.data_recebimento,
        status=ReceivableStatus(model.status),
    )


class SqlAlchemyAccountsReceivableRepository(AccountsReceivableRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AccountsReceivable | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel).where(
            AccountsReceivableModel.id == id, AccountsReceivableModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_invoice(self, fatura_id: uuid.UUID) -> list[AccountsReceivable]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(AccountsReceivableModel)
            .where(AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id)
            .order_by(AccountsReceivableModel.numero_parcela)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def exists_with_installment(self, fatura_id: uuid.UUID, numero_parcela: int) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel.id).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.numero_parcela == numero_parcela,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def count_pending_for_invoice(self, fatura_id: uuid.UUID, *, excluding_id: uuid.UUID | None = None) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel.id).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.status.in_([ReceivableStatus.PENDENTE.value, ReceivableStatus.VENCIDA.value]),
        )
        if excluding_id is not None:
            stmt = stmt.where(AccountsReceivableModel.id != excluding_id)
        return len((await self._session.execute(stmt)).all())

    async def sum_received_for_invoice(self, fatura_id: uuid.UUID) -> Decimal:
        tenant_id = get_current_tenant_id()
        stmt = select(func.coalesce(func.sum(AccountsReceivableModel.valor), 0)).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.status.in_([ReceivableStatus.RECEBIDA.value, ReceivableStatus.CONCILIADA.value]),
        )
        total = (await self._session.execute(stmt)).scalar_one()
        return Decimal(total)

    async def add(self, receivable: AccountsReceivable) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AccountsReceivableModel, receivable.id)
        if model is None:
            model = AccountsReceivableModel(id=receivable.id, tenant_id=tenant_id, fatura_id=receivable.fatura_id)
            self._session.add(model)
        model.numero_parcela = receivable.numero_parcela
        model.valor = receivable.valor
        model.data_vencimento = receivable.data_vencimento
        model.data_recebimento = receivable.data_recebimento
        model.status = receivable.status.value
        await self._session.flush()
