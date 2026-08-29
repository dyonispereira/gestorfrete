from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.checklist import Checklist
from modules.maintenance.domain.repositories.checklist_repository import ChecklistRepository
from modules.maintenance.domain.value_objects.checklist_referencia_tipo import ChecklistReferenciaTipo
from modules.maintenance.domain.value_objects.checklist_status import ChecklistStatus
from modules.maintenance.domain.value_objects.checklist_type import ChecklistType
from modules.maintenance.infrastructure.persistence.models.checklist_model import ChecklistModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: ChecklistModel) -> Checklist:
    return Checklist(
        id=model.id, codigo=model.codigo, tipo=ChecklistType(model.tipo),
        referencia_tipo=ChecklistReferenciaTipo(model.referencia_tipo), referencia_id=model.referencia_id,
        veiculo_tracionador_id=model.veiculo_tracionador_id, motorista_id=model.motorista_id,
        itens=list(model.itens), status=ChecklistStatus(model.status),
        checklist_reprovado_id=model.checklist_reprovado_id, criado_em=model.criado_em,
        atualizado_em=model.atualizado_em,
    )


class SqlAlchemyChecklistRepository(ChecklistRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Checklist | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ChecklistModel).where(ChecklistModel.id == id, ChecklistModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, referencia_tipo: str | None, referencia_id: uuid.UUID | None,
        tipo: str | None, status: str | None,
    ) -> tuple[list[Checklist], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ChecklistModel).where(ChecklistModel.tenant_id == tenant_id)
        if referencia_tipo is not None:
            stmt = stmt.where(ChecklistModel.referencia_tipo == referencia_tipo)
        if referencia_id is not None:
            stmt = stmt.where(ChecklistModel.referencia_id == referencia_id)
        if tipo is not None:
            stmt = stmt.where(ChecklistModel.tipo == tipo)
        if status is not None:
            stmt = stmt.where(ChecklistModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ChecklistModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Checklist) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ChecklistModel, aggregate.id)
        if model is None:
            model = ChecklistModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.tipo = aggregate.tipo.value
        model.referencia_tipo = aggregate.referencia_tipo.value
        model.referencia_id = aggregate.referencia_id
        model.veiculo_tracionador_id = aggregate.veiculo_tracionador_id
        model.motorista_id = aggregate.motorista_id
        model.itens = aggregate.itens
        model.status = aggregate.status.value
        model.checklist_reprovado_id = aggregate.checklist_reprovado_id
        model.criado_em = aggregate.criado_em
        model.atualizado_em = aggregate.atualizado_em
        await self._session.flush()

    async def find(self, specification: Specification[Checklist]) -> list[Checklist]:
        raise NotImplementedError("Use list_page — filtros de Checklist são resolvidos via SQL")
