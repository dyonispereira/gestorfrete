from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.vehicle_position import VehiclePosition
from modules.tracking.domain.repositories.vehicle_position_repository import VehiclePositionRepository
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.infrastructure.persistence.models.vehicle_position_model import VehiclePositionModel

# D404 — `ST_X`/`ST_Y` só existem para `geometry`, não `geography` (confirmado contra o Postgres
# real: `ST_X(geography)` levanta "não existe a função"). Todo cast passa por este tipo único.
_AS_GEOMETRY = Geometry(geometry_type=None)


def _row_to_entity(model: VehiclePositionModel, lon: float, lat: float) -> VehiclePosition:
    return VehiclePosition(
        id=model.id, veiculo_tracionador_id=model.veiculo_tracionador_id,
        equipamento_rastreamento_id=model.equipamento_rastreamento_id,
        localizacao=GeoPoint(latitude=lat, longitude=lon), origem_localizacao_id=model.origem_localizacao_id,
        precisao_metros=model.precisao_metros, numero_satelites=model.numero_satelites, hdop=model.hdop,
        nivel_confianca=model.nivel_confianca, capturado_em=model.capturado_em, recebido_em=model.recebido_em,
        processado_em=model.processado_em,
    )


class SqlAlchemyVehiclePositionRepository(VehiclePositionRepository):
    """Leitura de coordenadas sempre via `ST_X`/`ST_Y` explícitos (D404) — nunca via
    `model.localizacao` diretamente, o que exigiria desserializar WKB em Python (`shapely`,
    dependência deliberadamente não adicionada)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _select_with_coords(self) -> Any:
        geom = cast(VehiclePositionModel.localizacao, _AS_GEOMETRY)
        return select(VehiclePositionModel, func.ST_X(geom), func.ST_Y(geom))

    async def add(self, position: VehiclePosition) -> None:
        tenant_id = get_current_tenant_id()
        model = VehiclePositionModel(
            id=position.id, tenant_id=tenant_id, veiculo_tracionador_id=position.veiculo_tracionador_id,
            equipamento_rastreamento_id=position.equipamento_rastreamento_id,
            localizacao=f"SRID=4326;POINT({position.localizacao.longitude} {position.localizacao.latitude})",
            origem_localizacao_id=position.origem_localizacao_id, precisao_metros=position.precisao_metros,
            numero_satelites=position.numero_satelites, hdop=position.hdop,
            nivel_confianca=position.nivel_confianca, capturado_em=position.capturado_em,
            recebido_em=position.recebido_em, processado_em=position.processado_em,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_latest_for_vehicle(self, veiculo_tracionador_id: uuid.UUID) -> VehiclePosition | None:
        tenant_id = get_current_tenant_id()
        stmt = self._select_with_coords().where(
            VehiclePositionModel.tenant_id == tenant_id,
            VehiclePositionModel.veiculo_tracionador_id == veiculo_tracionador_id,
        ).order_by(VehiclePositionModel.capturado_em.desc(), VehiclePositionModel.id.desc()).limit(1)
        row = (await self._session.execute(stmt)).first()
        return _row_to_entity(row[0], row[1], row[2]) if row is not None else None

    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, after_capturado_em: datetime | None,
        after_id: uuid.UUID | None, limit: int, captured_at_gte: datetime | None,
        captured_at_lte: datetime | None, origin_id: uuid.UUID | None, equipment_id: uuid.UUID | None,
    ) -> list[VehiclePosition]:
        tenant_id = get_current_tenant_id()
        stmt = self._select_with_coords().where(
            VehiclePositionModel.tenant_id == tenant_id,
            VehiclePositionModel.veiculo_tracionador_id == veiculo_tracionador_id,
        )
        if captured_at_gte is not None:
            stmt = stmt.where(VehiclePositionModel.capturado_em >= captured_at_gte)
        if captured_at_lte is not None:
            stmt = stmt.where(VehiclePositionModel.capturado_em <= captured_at_lte)
        if origin_id is not None:
            stmt = stmt.where(VehiclePositionModel.origem_localizacao_id == origin_id)
        if equipment_id is not None:
            stmt = stmt.where(VehiclePositionModel.equipamento_rastreamento_id == equipment_id)
        if after_capturado_em is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    VehiclePositionModel.capturado_em < after_capturado_em,
                    and_(VehiclePositionModel.capturado_em == after_capturado_em, VehiclePositionModel.id < after_id),
                )
            )
        stmt = stmt.order_by(VehiclePositionModel.capturado_em.desc(), VehiclePositionModel.id.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).all()
        return [_row_to_entity(row[0], row[1], row[2]) for row in rows]
