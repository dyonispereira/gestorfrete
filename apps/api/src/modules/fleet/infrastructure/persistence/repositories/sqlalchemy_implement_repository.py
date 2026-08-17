from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.implement import Implement
from modules.fleet.domain.repositories.implement_repository import ImplementRepository
from modules.fleet.domain.value_objects.body_type import BodyType
from modules.fleet.domain.value_objects.implement_availability import ImplementAvailability
from modules.fleet.infrastructure.persistence.models.implement_model import ImplementModel
from modules.fleet.infrastructure.persistence.models.vehicle_composition_model import (
    VehicleCompositionModel,
    composicoes_veiculares_implementos,
)


def _to_entity(model: ImplementModel) -> Implement:
    return Implement(
        id=model.id,
        codigo=model.codigo,
        placa=model.placa,
        renavam=model.renavam,
        tipo_carroceria=BodyType(model.tipo_carroceria),
        categoria_veiculo_id=model.categoria_veiculo_id,
        capacidade_carga=model.capacidade_carga,
        status_disponibilidade=ImplementAvailability(model.status_disponibilidade),
        created_at=model.criado_em,
        updated_at=model.atualizado_em,
        deleted_at=model.excluido_em,
    )


class SqlAlchemyImplementRepository(ImplementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Implement | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ImplementModel).where(
            ImplementModel.id == id, ImplementModel.tenant_id == tenant_id, ImplementModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_placa(self, placa: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ImplementModel.id).where(ImplementModel.tenant_id == tenant_id, ImplementModel.placa == placa)
        if excluding_id is not None:
            stmt = stmt.where(ImplementModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self, *, page: int, limit: int, search: str | None, tipo_carroceria: str | None, status: str | None
    ) -> tuple[list[Implement], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ImplementModel).where(ImplementModel.tenant_id == tenant_id, ImplementModel.excluido_em.is_(None))
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(ImplementModel.placa.ilike(like) | ImplementModel.codigo.ilike(like))
        if tipo_carroceria is not None:
            stmt = stmt.where(ImplementModel.tipo_carroceria == tipo_carroceria)
        if status is not None:
            stmt = stmt.where(ImplementModel.status_disponibilidade == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ImplementModel.placa).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, implement: Implement) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ImplementModel, implement.id)
        if model is None:
            model = ImplementModel(id=implement.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = implement.codigo
        model.placa = implement.placa
        model.renavam = implement.renavam
        model.tipo_carroceria = implement.tipo_carroceria.value
        model.categoria_veiculo_id = implement.categoria_veiculo_id
        model.capacidade_carga = implement.capacidade_carga
        model.status_disponibilidade = implement.status_disponibilidade.value
        model.criado_em = implement.created_at
        model.atualizado_em = implement.updated_at
        model.excluido_em = implement.deleted_at
        await self._session.flush()

    async def exists_in_active_composition(self, implement_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(composicoes_veiculares_implementos.c.implemento_id)
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
        return (await self._session.execute(stmt)).first() is not None
