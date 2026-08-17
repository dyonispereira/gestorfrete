from __future__ import annotations

import json
import uuid
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.tracking.domain.entities.geofence import Geofence
from modules.tracking.domain.repositories.geofence_repository import GeofenceRepository
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.geofence_geometry_type import GeofenceGeometryType
from modules.tracking.domain.value_objects.geofence_status import GeofenceStatus
from modules.tracking.infrastructure.persistence.models.geofence_model import GeofenceModel
from modules.tracking.infrastructure.persistence.models.tracking_event_model import TrackingEventModel

_AS_GEOMETRY = Geometry(geometry_type=None)


def _polygon_from_geojson(geojson: str | None) -> list[GeoPoint] | None:
    if geojson is None:
        return None
    coordinates = json.loads(geojson)["coordinates"][0]
    return [GeoPoint(latitude=lat, longitude=lon) for lon, lat in coordinates]


def _row_to_entity(model: GeofenceModel, centro_lon: float | None, centro_lat: float | None, poligono_geojson: str | None) -> Geofence:
    centro = GeoPoint(latitude=centro_lat, longitude=centro_lon) if centro_lon is not None and centro_lat is not None else None
    return Geofence(
        id=model.id, nome=model.nome, tipo_geometria=GeofenceGeometryType(model.tipo_geometria), centro=centro,
        raio_metros=model.raio_metros, poligono=_polygon_from_geojson(poligono_geojson),
        cliente_id=model.cliente_id, filial_id=model.filial_id, status=GeofenceStatus(model.status),
    )


class SqlAlchemyGeofenceRepository(GeofenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _select_with_geometry(self) -> Any:
        centro_geom = cast(GeofenceModel.centro, _AS_GEOMETRY)
        return select(
            GeofenceModel, func.ST_X(centro_geom), func.ST_Y(centro_geom),
            func.ST_AsGeoJSON(cast(GeofenceModel.poligono, _AS_GEOMETRY)),
        )

    async def get_by_id(self, id: uuid.UUID) -> Geofence | None:
        tenant_id = get_current_tenant_id()
        stmt = self._select_with_geometry().where(GeofenceModel.id == id, GeofenceModel.tenant_id == tenant_id)
        row = (await self._session.execute(stmt)).first()
        return _row_to_entity(row[0], row[1], row[2], row[3]) if row is not None else None

    async def get_by_nome(self, nome: str) -> Geofence | None:
        tenant_id = get_current_tenant_id()
        stmt = self._select_with_geometry().where(GeofenceModel.tenant_id == tenant_id, GeofenceModel.nome == nome)
        row = (await self._session.execute(stmt)).first()
        return _row_to_entity(row[0], row[1], row[2], row[3]) if row is not None else None

    async def list_active_ids_containing(self, point: GeoPoint) -> list[uuid.UUID]:
        tenant_id = get_current_tenant_id()
        # `ST_GeogFromText` explícito — sem ele, asyncpg prepara o parâmetro como VARCHAR (tipo
        # inferido do literal Python) e o Postgres rejeita `ST_DWithin(geography, varchar, numeric)`
        # por não existir essa sobrecarga (achado real, só visível rodando contra o Postgres de
        # verdade, nunca em mock).
        ponto = func.ST_GeogFromText(f"SRID=4326;POINT({point.longitude} {point.latitude})")
        stmt = select(GeofenceModel.id).where(
            GeofenceModel.tenant_id == tenant_id, GeofenceModel.status == GeofenceStatus.ATIVA.value,
            or_(
                func.ST_DWithin(GeofenceModel.centro, ponto, GeofenceModel.raio_metros),
                func.ST_Covers(GeofenceModel.poligono, ponto),
            ),
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_page(
        self, *, page: int, limit: int, search: str | None, geometry_type: str | None,
        client_id: uuid.UUID | None, branch_id: uuid.UUID | None, status: str | None,
    ) -> tuple[list[Geofence], int]:
        tenant_id = get_current_tenant_id()
        filters = [GeofenceModel.tenant_id == tenant_id]
        if search is not None:
            filters.append(GeofenceModel.nome.ilike(f"%{search}%"))
        if geometry_type is not None:
            filters.append(GeofenceModel.tipo_geometria == geometry_type)
        if client_id is not None:
            filters.append(GeofenceModel.cliente_id == client_id)
        if branch_id is not None:
            filters.append(GeofenceModel.filial_id == branch_id)
        if status is not None:
            filters.append(GeofenceModel.status == status)

        count_stmt = select(func.count()).select_from(GeofenceModel).where(*filters)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            self._select_with_geometry().where(*filters)
            .order_by(GeofenceModel.nome.asc()).offset((page - 1) * limit).limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [_row_to_entity(row[0], row[1], row[2], row[3]) for row in rows], total

    async def add(self, geofence: Geofence) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(GeofenceModel, geofence.id)
        if model is None:
            model = GeofenceModel(id=geofence.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome = geofence.nome
        model.tipo_geometria = geofence.tipo_geometria.value
        model.centro = (
            f"SRID=4326;POINT({geofence.centro.longitude} {geofence.centro.latitude})"
            if geofence.centro is not None else None
        )
        model.raio_metros = geofence.raio_metros
        model.poligono = (
            "SRID=4326;POLYGON((" + ",".join(f"{p.longitude} {p.latitude}" for p in geofence.poligono) + "))"
            if geofence.poligono else None
        )
        model.cliente_id = geofence.cliente_id
        model.filial_id = geofence.filial_id
        model.status = geofence.status.value
        await self._session.flush()

    async def is_referenced_by_recent_events(self, id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(TrackingEventModel.id).where(
            TrackingEventModel.tenant_id == tenant_id, TrackingEventModel.cerca_eletronica_id == id
        ).limit(1)
        return (await self._session.execute(stmt)).first() is not None

    async def delete(self, geofence: Geofence) -> None:
        geofence.update(
            nome=None, tipo_geometria=None, centro=None, raio_metros=None, poligono=None,
            cliente_id=None, filial_id=None, status=GeofenceStatus.INATIVA,
        )
        await self.add(geofence)
