from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.bank_account import BankAccount
from modules.financial.domain.repositories.bank_account_repository import BankAccountRepository
from modules.financial.domain.value_objects.bank_account_status import BankAccountStatus
from modules.financial.domain.value_objects.bank_account_type import BankAccountType
from modules.financial.domain.value_objects.payable_status import PayableStatus
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.models.accounts_payable_model import AccountsPayableModel
from modules.financial.infrastructure.persistence.models.accounts_receivable_model import AccountsReceivableModel
from modules.financial.infrastructure.persistence.models.bank_account_model import BankAccountModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: BankAccountModel) -> BankAccount:
    return BankAccount(
        id=model.id, banco=model.banco, agencia=model.agencia, numero_conta=model.numero_conta,
        tipo=BankAccountType(model.tipo), status=BankAccountStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em, created_by=model.criado_por, updated_at=model.atualizado_em,
            updated_by=model.atualizado_por, deleted_at=model.excluido_em, deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyBankAccountRepository(BankAccountRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> BankAccount | None:
        tenant_id = get_current_tenant_id()
        stmt = select(BankAccountModel).where(
            BankAccountModel.id == id, BankAccountModel.tenant_id == tenant_id, BankAccountModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_numero_conta(self, numero_conta: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(BankAccountModel.id).where(
            BankAccountModel.tenant_id == tenant_id, BankAccountModel.numero_conta == numero_conta
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, status: str | None, tipo: str | None
    ) -> tuple[list[BankAccount], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(BankAccountModel).where(
            BankAccountModel.tenant_id == tenant_id, BankAccountModel.excluido_em.is_(None)
        )
        if status is not None:
            stmt = stmt.where(BankAccountModel.status == status)
        if tipo is not None:
            stmt = stmt.where(BankAccountModel.tipo == tipo)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(BankAccountModel.banco).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def calculate_tenant_balance(self) -> Decimal:
        tenant_id = get_current_tenant_id()
        received_stmt = (
            select(func.coalesce(func.sum(AccountsReceivableModel.valor), 0))
            .select_from(AccountsReceivableModel)
            .where(
                AccountsReceivableModel.tenant_id == tenant_id,
                AccountsReceivableModel.status.in_([ReceivableStatus.RECEBIDA.value, ReceivableStatus.CONCILIADA.value]),
            )
        )
        paid_stmt = (
            select(func.coalesce(func.sum(AccountsPayableModel.valor), 0))
            .select_from(AccountsPayableModel)
            .where(
                AccountsPayableModel.tenant_id == tenant_id,
                AccountsPayableModel.status.in_([PayableStatus.PAGA.value, PayableStatus.CONCILIADA.value]),
            )
        )
        received = (await self._session.execute(received_stmt)).scalar_one()
        paid = (await self._session.execute(paid_stmt)).scalar_one()
        return Decimal(received) - Decimal(paid)

    async def add(self, aggregate: BankAccount) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(BankAccountModel, aggregate.id)
        if model is None:
            model = BankAccountModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.banco = aggregate.banco
        model.agencia = aggregate.agencia
        model.numero_conta = aggregate.numero_conta
        model.tipo = aggregate.tipo.value
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[BankAccount]) -> list[BankAccount]:
        raise NotImplementedError("Use list_page — filtros de BankAccount são resolvidos via SQL")
