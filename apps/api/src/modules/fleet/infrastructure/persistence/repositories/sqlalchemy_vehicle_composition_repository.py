from __future__ import annotations

import uuid

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_composition import VehicleComposition
from modules.fleet.domain.repositories.vehicle_composition_repository import VehicleCompositionRepository
from modules.fleet.domain.value_objects.combination_type import CombinationType
from modules.fleet.domain.value_objects.composition_status import CompositionStatus
from modules.fleet.infrastructure.persistence.models.vehicle_composition_model import (
    VehicleCompositionModel,
    composicoes_veiculares_implementos,
)


async def _implementos_for(session: AsyncSession, composicao_id: uuid.UUID) -> list[tuple[uuid.UUID, int]]:
    stmt = (
        select(composicoes_veiculares_implementos.c.implemento_id, composicoes_veiculares_implementos.c.ordem)
        .where(composicoes_veiculares_implementos.c.composicao_veicular_id == composicao_id)
        .order_by(composicoes_veiculares_implementos.c.ordem)
    )
    rows = (await session.execute(stmt)).all()
    return [(row.implemento_id, row.ordem) for row in rows]


async def _to_entity(session: AsyncSession, model: VehicleCompositionModel) -> VehicleComposition:
    return VehicleComposition(
        id=model.id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        tipo_combinacao=CombinationType(model.tipo_combinacao),
        eixos_total=model.eixos_total,
        status=CompositionStatus(model.status),
        implementos=await _implementos_for(session, model.id),
        data_inicio_vigencia=model.data_inicio_vigencia,
        data_fim_vigencia=model.data_fim_vigencia,
        alterado_por=model.alterado_por,
    )


class SqlAlchemyVehicleCompositionRepository(VehicleCompositionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> VehicleComposition | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCompositionModel).where(
            VehicleCompositionModel.id == id, VehicleCompositionModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return await _to_entity(self._session, model) if model is not None else None

    async def get_current_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> VehicleComposition | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCompositionModel).where(
            VehicleCompositionModel.tenant_id == tenant_id,
            VehicleCompositionModel.veiculo_tracionador_id == veiculo_tracionador_id,
            VehicleCompositionModel.data_fim_vigencia.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return await _to_entity(self._session, model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, veiculo_tracionador_id: uuid.UUID | None, tipo_combinacao: str | None, vigente: bool
    ) -> tuple[list[VehicleComposition], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleCompositionModel).where(VehicleCompositionModel.tenant_id == tenant_id)
        if veiculo_tracionador_id is not None:
            stmt = stmt.where(VehicleCompositionModel.veiculo_tracionador_id == veiculo_tracionador_id)
        if tipo_combinacao is not None:
            stmt = stmt.where(VehicleCompositionModel.tipo_combinacao == tipo_combinacao)
        stmt = stmt.where(
            VehicleCompositionModel.data_fim_vigencia.is_(None)
            if vigente
            else VehicleCompositionModel.data_fim_vigencia.is_not(None)
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleCompositionModel.data_inicio_vigencia.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [await _to_entity(self._session, m) for m in models], total

    async def add(self, composition: VehicleComposition) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleCompositionModel, composition.id)
        if model is None:
            model = VehicleCompositionModel(
                id=composition.id, tenant_id=tenant_id, veiculo_tracionador_id=composition.veiculo_tracionador_id
            )
            self._session.add(model)
        model.tipo_combinacao = composition.tipo_combinacao.value
        model.eixos_total = composition.eixos_total
        model.status = composition.status.value
        model.data_inicio_vigencia = composition.data_inicio_vigencia
        model.data_fim_vigencia = composition.data_fim_vigencia
        model.alterado_por = composition.alterado_por
        await self._session.flush()

        current = {implemento_id for implemento_id, _ in await _implementos_for(self._session, composition.id)}
        target = {implemento_id for implemento_id, _ in composition.implementos}
        to_remove = current - target
        if to_remove:
            await self._session.execute(
                delete(composicoes_veiculares_implementos).where(
                    composicoes_veiculares_implementos.c.composicao_veicular_id == composition.id,
                    composicoes_veiculares_implementos.c.implemento_id.in_(to_remove),
                )
            )
        to_add = [(implemento_id, ordem) for implemento_id, ordem in composition.implementos if implemento_id not in current]
        if to_add:
            await self._session.execute(
                insert(composicoes_veiculares_implementos),
                [
                    {"composicao_veicular_id": composition.id, "implemento_id": implemento_id, "ordem": ordem}
                    for implemento_id, ordem in to_add
                ],
            )

    async def count_active_for_implement(self, implement_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(func.count())
            .select_from(composicoes_veiculares_implementos)
            .join(
                VehicleCompositionModel,
                VehicleCompositionModel.id == composicoes_veiculares_implementos.c.composicao_veicular_id,
            )
            .where(
                composicoes_veiculares_implementos.c.implemento_id == implement_id,
                VehicleCompositionModel.tenant_id == tenant_id,
                VehicleCompositionModel.data_fim_vigencia.is_(None),
            )
        )
        return (await self._session.execute(stmt)).scalar_one()
