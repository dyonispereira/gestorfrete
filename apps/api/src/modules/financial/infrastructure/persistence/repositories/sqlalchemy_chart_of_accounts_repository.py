from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.chart_of_accounts import ChartOfAccounts
from modules.financial.domain.repositories.chart_of_accounts_repository import ChartOfAccountsRepository
from modules.financial.domain.value_objects.chart_of_accounts_status import ChartOfAccountsStatus
from modules.financial.domain.value_objects.chart_of_accounts_type import ChartOfAccountsType
from modules.financial.infrastructure.persistence.models.accounts_payable_model import AccountsPayableModel
from modules.financial.infrastructure.persistence.models.chart_of_accounts_model import ChartOfAccountsModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: ChartOfAccountsModel) -> ChartOfAccounts:
    return ChartOfAccounts(
        id=model.id,
        codigo_contabil=model.codigo_contabil,
        nome=model.nome,
        tipo=ChartOfAccountsType(model.tipo),
        categoria_pai_id=model.categoria_pai_id,
        status=ChartOfAccountsStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em, created_by=model.criado_por, updated_at=model.atualizado_em,
            updated_by=model.atualizado_por, deleted_at=model.excluido_em, deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyChartOfAccountsRepository(ChartOfAccountsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ChartOfAccounts | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ChartOfAccountsModel).where(
            ChartOfAccountsModel.id == id, ChartOfAccountsModel.tenant_id == tenant_id,
            ChartOfAccountsModel.excluido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_codigo(self, codigo_contabil: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ChartOfAccountsModel.id).where(
            ChartOfAccountsModel.tenant_id == tenant_id, ChartOfAccountsModel.codigo_contabil == codigo_contabil
        )
        if excluding_id is not None:
            stmt = stmt.where(ChartOfAccountsModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def has_active_children(self, parent_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ChartOfAccountsModel.id).where(
            ChartOfAccountsModel.tenant_id == tenant_id, ChartOfAccountsModel.categoria_pai_id == parent_id,
            ChartOfAccountsModel.status == ChartOfAccountsStatus.ATIVO.value,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def is_descendant_of(self, candidate_ancestor_id: uuid.UUID, node_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        current_id: uuid.UUID | None = node_id
        visited: set[uuid.UUID] = set()
        while current_id is not None:
            if current_id in visited:
                return False  # já era um ciclo por outra causa — não é o alvo desta checagem
            visited.add(current_id)
            stmt = select(ChartOfAccountsModel.categoria_pai_id).where(
                ChartOfAccountsModel.id == current_id, ChartOfAccountsModel.tenant_id == tenant_id
            )
            parent_id = (await self._session.execute(stmt)).scalar_one_or_none()
            if parent_id == candidate_ancestor_id:
                return True
            current_id = parent_id
        return False

    async def is_referenced_by_payables(self, id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsPayableModel.id).where(
            AccountsPayableModel.tenant_id == tenant_id, AccountsPayableModel.plano_contas_id == id
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, tipo: str | None, parent_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[ChartOfAccounts], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ChartOfAccountsModel).where(
            ChartOfAccountsModel.tenant_id == tenant_id, ChartOfAccountsModel.excluido_em.is_(None)
        )
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(ChartOfAccountsModel.nome.ilike(like) | ChartOfAccountsModel.codigo_contabil.ilike(like))
        if tipo is not None:
            stmt = stmt.where(ChartOfAccountsModel.tipo == tipo)
        if parent_id is not None:
            stmt = stmt.where(ChartOfAccountsModel.categoria_pai_id == parent_id)
        if status is not None:
            stmt = stmt.where(ChartOfAccountsModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ChartOfAccountsModel.codigo_contabil).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: ChartOfAccounts) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ChartOfAccountsModel, aggregate.id)
        if model is None:
            model = ChartOfAccountsModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo_contabil = aggregate.codigo_contabil
        model.nome = aggregate.nome
        model.tipo = aggregate.tipo.value
        model.categoria_pai_id = aggregate.categoria_pai_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[ChartOfAccounts]) -> list[ChartOfAccounts]:
        raise NotImplementedError("Use list_page — filtros de ChartOfAccounts são resolvidos via SQL")
