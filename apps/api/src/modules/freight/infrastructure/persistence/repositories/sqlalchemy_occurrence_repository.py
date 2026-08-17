from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.occurrence import Occurrence
from modules.freight.domain.repositories.occurrence_repository import OccurrenceRepository
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_status import OccurrenceStatus
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from modules.freight.infrastructure.persistence.models.occurrence_model import OccurrenceModel


def _to_entity(model: OccurrenceModel) -> Occurrence:
    return Occurrence(
        id=model.id,
        viagem_id=model.viagem_id,
        tipo=OccurrenceType(model.tipo),
        descricao=model.descricao,
        gravidade=OccurrenceSeverity(model.gravidade) if model.gravidade else None,
        status=OccurrenceStatus(model.status),
        data_hora=model.data_hora,
    )


class SqlAlchemyOccurrenceRepository(OccurrenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Occurrence | None:
        tenant_id = get_current_tenant_id()
        stmt = select(OccurrenceModel).where(OccurrenceModel.id == id, OccurrenceModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page_for_trip(
        self,
        viagem_id: uuid.UUID,
        *,
        page: int,
        limit: int,
        tipo: str | None,
        status: str | None,
        gravidade: str | None,
    ) -> tuple[list[Occurrence], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id, OccurrenceModel.viagem_id == viagem_id)
        if tipo is not None:
            stmt = stmt.where(OccurrenceModel.tipo == tipo)
        if status is not None:
            stmt = stmt.where(OccurrenceModel.status == status)
        if gravidade is not None:
            stmt = stmt.where(OccurrenceModel.gravidade == gravidade)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(OccurrenceModel.data_hora.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Occurrence) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(OccurrenceModel, aggregate.id)
        if model is None:
            model = OccurrenceModel(id=aggregate.id, tenant_id=tenant_id, viagem_id=aggregate.viagem_id)
            self._session.add(model)
        model.tipo = aggregate.tipo.value
        model.descricao = aggregate.descricao
        model.gravidade = aggregate.gravidade.value if aggregate.gravidade else None
        model.status = aggregate.status.value
        model.data_hora = aggregate.data_hora
        await self._session.flush()
