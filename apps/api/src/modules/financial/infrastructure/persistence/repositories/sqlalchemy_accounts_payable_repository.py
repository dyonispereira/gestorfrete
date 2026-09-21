from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.accounts_payable import AccountsPayable
from modules.financial.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.domain.value_objects.payable_status import PayableStatus
from modules.financial.infrastructure.persistence.models.accounts_payable_model import AccountsPayableModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: AccountsPayableModel) -> AccountsPayable:
    return AccountsPayable(
        id=model.id, fornecedor_id=model.fornecedor_id, centro_custo_id=model.centro_custo_id,
        origem=PayableOrigin(model.origem), viagem_id=model.viagem_id, ordem_servico_id=model.ordem_servico_id,
        veiculo_tracionador_id=model.veiculo_tracionador_id, motorista_id=model.motorista_id,
        valor=model.valor, data_vencimento=model.data_vencimento, competencia=model.competencia,
        plano_contas_id=model.plano_contas_id, status=PayableStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em, created_by=model.criado_por, updated_at=model.atualizado_em,
            updated_by=model.atualizado_por, deleted_at=model.excluido_em, deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyAccountsPayableRepository(AccountsPayableRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AccountsPayable | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsPayableModel).where(
            AccountsPayableModel.id == id, AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        origin: str | None,
        supplier_id: uuid.UUID | None,
        cost_center_id: uuid.UUID | None,
        trip_id: uuid.UUID | None,
        vehicle_id: uuid.UUID | None,
        chart_of_accounts_id: uuid.UUID | None,
        accounting_period: date | None,
        due_date_from: date | None,
        due_date_to: date | None,
    ) -> tuple[list[AccountsPayable], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsPayableModel).where(
            AccountsPayableModel.tenant_id == tenant_id, AccountsPayableModel.excluido_em.is_(None)
        )
        if status is not None:
            stmt = stmt.where(AccountsPayableModel.status == status)
        if origin is not None:
            stmt = stmt.where(AccountsPayableModel.origem == origin)
        if supplier_id is not None:
            stmt = stmt.where(AccountsPayableModel.fornecedor_id == supplier_id)
        if cost_center_id is not None:
            stmt = stmt.where(AccountsPayableModel.centro_custo_id == cost_center_id)
        if trip_id is not None:
            stmt = stmt.where(AccountsPayableModel.viagem_id == trip_id)
        if vehicle_id is not None:
            stmt = stmt.where(AccountsPayableModel.veiculo_tracionador_id == vehicle_id)
        if chart_of_accounts_id is not None:
            stmt = stmt.where(AccountsPayableModel.plano_contas_id == chart_of_accounts_id)
        if accounting_period is not None:
            stmt = stmt.where(AccountsPayableModel.competencia == accounting_period)
        if due_date_from is not None:
            stmt = stmt.where(AccountsPayableModel.data_vencimento >= due_date_from)
        if due_date_to is not None:
            stmt = stmt.where(AccountsPayableModel.data_vencimento <= due_date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AccountsPayableModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: AccountsPayable) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AccountsPayableModel, aggregate.id)
        if model is None:
            model = AccountsPayableModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.fornecedor_id = aggregate.fornecedor_id
        model.centro_custo_id = aggregate.centro_custo_id
        model.origem = aggregate.origem.value
        model.viagem_id = aggregate.viagem_id
        model.ordem_servico_id = aggregate.ordem_servico_id
        model.veiculo_tracionador_id = aggregate.veiculo_tracionador_id
        model.motorista_id = aggregate.motorista_id
        model.valor = aggregate.valor
        model.data_vencimento = aggregate.data_vencimento
        model.competencia = aggregate.competencia
        model.plano_contas_id = aggregate.plano_contas_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[AccountsPayable]) -> list[AccountsPayable]:
        raise NotImplementedError("Use list_page — filtros de AccountsPayable são resolvidos via SQL")

    async def exists_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsPayableModel.id).where(
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.ordem_servico_id == ordem_servico_id,
            AccountsPayableModel.excluido_em.is_(None),
        )
        return (await self._session.execute(stmt)).first() is not None
