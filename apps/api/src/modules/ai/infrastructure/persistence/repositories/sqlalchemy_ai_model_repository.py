from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.ai.domain.entities.ai_model import AIModel
from modules.ai.domain.repositories.ai_model_repository import AIModelRepository
from modules.ai.domain.value_objects.logical_provider import LogicalProvider
from modules.ai.domain.value_objects.model_status import ModelStatus
from modules.ai.domain.value_objects.model_type import ModelType
from modules.ai.infrastructure.persistence.models.ai_model_model import AIModelModel


def _to_entity(model: AIModelModel) -> AIModel:
    return AIModel(
        id=model.id, tenant_id=model.tenant_id, nome=model.nome, tipo=ModelType(model.tipo),
        versao=model.versao, fornecedor_logico=LogicalProvider(model.fornecedor_logico),
        capacidade=model.capacidade, contexto_maximo=model.contexto_maximo, status=ModelStatus(model.status),
    )


class SqlAlchemyAIModelRepository(AIModelRepository):
    """Mesmo tratamento de Platform Reference Data de `SqlAlchemyMetricRepository` (D046) —
    `tenant_id IS NULL` sempre visível, além do escopo do próprio tenant."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AIModel | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AIModelModel).where(
            AIModelModel.id == id, or_(AIModelModel.tenant_id == tenant_id, AIModelModel.tenant_id.is_(None))
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_name_and_version(self, nome: str, versao: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AIModelModel.id).where(
            AIModelModel.nome == nome, AIModelModel.versao == versao,
            or_(AIModelModel.tenant_id == tenant_id, AIModelModel.tenant_id.is_(None)),
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, tipo: str | None, fornecedor_logico: str | None, status: str | None,
    ) -> tuple[list[AIModel], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(AIModelModel).where(
            or_(AIModelModel.tenant_id == tenant_id, AIModelModel.tenant_id.is_(None))
        )
        if tipo is not None:
            stmt = stmt.where(AIModelModel.tipo == tipo)
        if fornecedor_logico is not None:
            stmt = stmt.where(AIModelModel.fornecedor_logico == fornecedor_logico)
        if status is not None:
            stmt = stmt.where(AIModelModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AIModelModel.nome, AIModelModel.versao).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, model: AIModel) -> None:
        tenant_id = model.tenant_id if model.tenant_id is not None else get_current_tenant_id()
        row = await self._session.get(AIModelModel, model.id)
        if row is None:
            row = AIModelModel(id=model.id, tenant_id=tenant_id)
            self._session.add(row)
        row.nome = model.nome
        row.tipo = model.tipo.value
        row.versao = model.versao
        row.fornecedor_logico = model.fornecedor_logico.value
        row.capacidade = model.capacidade
        row.contexto_maximo = model.contexto_maximo
        row.status = model.status.value
        await self._session.flush()
