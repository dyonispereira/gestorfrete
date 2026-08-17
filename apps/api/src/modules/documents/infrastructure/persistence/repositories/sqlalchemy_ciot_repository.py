from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.ciot import Ciot
from modules.documents.domain.repositories.ciot_repository import CiotRepository
from modules.documents.domain.value_objects.ciot_status import CiotStatus
from modules.documents.infrastructure.persistence.models.ciot_model import CiotModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: CiotModel) -> Ciot:
    return Ciot(
        id=model.id, viagem_id=model.viagem_id, motorista_id=model.motorista_id,
        codigo_ciot=model.codigo_ciot, status=CiotStatus(model.status), protocolo_antt=model.protocolo_antt,
        data_hora_registro=model.data_hora_registro,
    )


class SqlAlchemyCiotRepository(CiotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Ciot | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CiotModel).where(CiotModel.id == id, CiotModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_protocolo_antt(self, protocolo_antt: str) -> Ciot | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CiotModel).where(CiotModel.tenant_id == tenant_id, CiotModel.protocolo_antt == protocolo_antt)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, motorista_id: uuid.UUID | None,
        status: str | None,
    ) -> tuple[list[Ciot], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(CiotModel).where(CiotModel.tenant_id == tenant_id)
        if viagem_id is not None:
            stmt = stmt.where(CiotModel.viagem_id == viagem_id)
        if motorista_id is not None:
            stmt = stmt.where(CiotModel.motorista_id == motorista_id)
        if status is not None:
            stmt = stmt.where(CiotModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(CiotModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Ciot) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(CiotModel, aggregate.id)
        if model is None:
            model = CiotModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.viagem_id = aggregate.viagem_id
        model.motorista_id = aggregate.motorista_id
        model.codigo_ciot = aggregate.codigo_ciot
        model.status = aggregate.status.value
        model.protocolo_antt = aggregate.protocolo_antt
        model.data_hora_registro = aggregate.data_hora_registro
        await self._session.flush()

    async def find(self, specification: Specification[Ciot]) -> list[Ciot]:
        raise NotImplementedError("Use list_page — filtros de Ciot são resolvidos via SQL")
