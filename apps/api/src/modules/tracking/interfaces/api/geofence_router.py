from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.commands.create_geofence import CreateGeofenceCommand, CreateGeofenceHandler
from modules.tracking.application.commands.create_speed_limit_config import (
    CreateSpeedLimitConfigCommand,
    CreateSpeedLimitConfigHandler,
)
from modules.tracking.application.commands.delete_geofence import DeleteGeofenceCommand, DeleteGeofenceHandler
from modules.tracking.application.commands.update_geofence import UpdateGeofenceCommand, UpdateGeofenceHandler
from modules.tracking.application.commands.update_speed_limit_config import (
    UpdateSpeedLimitConfigCommand,
    UpdateSpeedLimitConfigHandler,
)
from modules.tracking.application.queries.get_geofence import GetGeofenceHandler, GetGeofenceQuery
from modules.tracking.application.queries.get_speed_limit_config import (
    GetSpeedLimitConfigHandler,
    GetSpeedLimitConfigQuery,
)
from modules.tracking.application.queries.list_geofences import ListGeofencesHandler, ListGeofencesQuery
from modules.tracking.application.queries.list_speed_limit_configs import (
    ListSpeedLimitConfigsHandler,
    ListSpeedLimitConfigsQuery,
)
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.geofence_geometry_type import GeofenceGeometryType
from modules.tracking.domain.value_objects.geofence_status import GeofenceStatus
from modules.tracking.domain.value_objects.speed_limit_config_status import SpeedLimitConfigStatus
from modules.tracking.interfaces.schemas.geo_point_schema import GeoPointSchema
from modules.tracking.interfaces.schemas.geofence_schemas import (
    CreateGeofenceRequest,
    CreateSpeedLimitConfigRequest,
    GeofenceResponse,
    SpeedLimitConfigResponse,
    UpdateGeofenceRequest,
    UpdateSpeedLimitConfigRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tracking/geofences", tags=["Geofences"])
speed_limit_router = APIRouter(prefix="/tracking/speed-limit-configs", tags=["Speed Limit Configs"])


def _points(schema_points: list[GeoPointSchema] | None) -> list[GeoPoint] | None:
    return [GeoPoint(latitude=p.latitude, longitude=p.longitude) for p in schema_points] if schema_points else None


@router.get("")
async def list_geofences(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    geometry_type: str | None = None,
    client_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.geofence.view")),
) -> dict[str, Any]:
    handler = ListGeofencesHandler(get_session_factory())
    result = await handler.handle(
        ListGeofencesQuery(
            actor=actor, page=page, limit=limit, search=search, geometry_type=geometry_type,
            client_id=client_id, branch_id=branch_id, status=status,
        )
    )
    return {
        "data": [GeofenceResponse.from_dto(g) for g in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
    geofence_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("tracking.geofence.view"))
) -> GeofenceResponse:
    handler = GetGeofenceHandler(get_session_factory())
    dto = await handler.handle(GetGeofenceQuery(actor=actor, geofence_id=geofence_id))
    return GeofenceResponse.from_dto(dto)


@router.post("", response_model=GeofenceResponse, status_code=201)
async def create_geofence(
    body: CreateGeofenceRequest, actor: AuthenticatedActor = Depends(require_permission("tracking.geofence.create"))
) -> GeofenceResponse:
    handler = CreateGeofenceHandler()
    center = GeoPoint(latitude=body.center.latitude, longitude=body.center.longitude) if body.center else None
    dto = await handler.handle(
        CreateGeofenceCommand(
            actor=actor, name=body.name, geometry_type=GeofenceGeometryType(body.geometry_type), center=center,
            radius_meters=body.radius_meters, polygon=_points(body.polygon), client_id=body.client_id,
            branch_id=body.branch_id,
        )
    )
    return GeofenceResponse.from_dto(dto)


@router.patch("/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: uuid.UUID, body: UpdateGeofenceRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.geofence.edit")),
) -> GeofenceResponse:
    handler = UpdateGeofenceHandler()
    center = GeoPoint(latitude=body.center.latitude, longitude=body.center.longitude) if body.center else None
    geometry_type = GeofenceGeometryType(body.geometry_type) if body.geometry_type is not None else None
    status = GeofenceStatus(body.status) if body.status is not None else None
    dto = await handler.handle(
        UpdateGeofenceCommand(
            actor=actor, geofence_id=geofence_id, name=body.name, geometry_type=geometry_type, center=center,
            radius_meters=body.radius_meters, polygon=_points(body.polygon), client_id=body.client_id,
            branch_id=body.branch_id, status=status,
        )
    )
    return GeofenceResponse.from_dto(dto)


@router.delete("/{geofence_id}", status_code=204, response_model=None)
async def delete_geofence(
    geofence_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("tracking.geofence.delete"))
) -> None:
    handler = DeleteGeofenceHandler()
    await handler.handle(DeleteGeofenceCommand(actor=actor, geofence_id=geofence_id))


@speed_limit_router.get("")
async def list_speed_limit_configs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    vehicle_category_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("tracking.speed_limit_config.view")),
) -> dict[str, Any]:
    handler = ListSpeedLimitConfigsHandler(get_session_factory())
    result = await handler.handle(
        ListSpeedLimitConfigsQuery(
            actor=actor, page=page, limit=limit, vehicle_category_id=vehicle_category_id, status=status
        )
    )
    return {
        "data": [SpeedLimitConfigResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@speed_limit_router.get("/{speed_limit_config_id}", response_model=SpeedLimitConfigResponse)
async def get_speed_limit_config(
    speed_limit_config_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("tracking.speed_limit_config.view")),
) -> SpeedLimitConfigResponse:
    handler = GetSpeedLimitConfigHandler(get_session_factory())
    dto = await handler.handle(GetSpeedLimitConfigQuery(actor=actor, speed_limit_config_id=speed_limit_config_id))
    return SpeedLimitConfigResponse.from_dto(dto)


@speed_limit_router.post("", response_model=SpeedLimitConfigResponse, status_code=201)
async def create_speed_limit_config(
    body: CreateSpeedLimitConfigRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.speed_limit_config.create")),
) -> SpeedLimitConfigResponse:
    handler = CreateSpeedLimitConfigHandler()
    dto = await handler.handle(
        CreateSpeedLimitConfigCommand(
            actor=actor, vehicle_category_id=body.vehicle_category_id, limit_kmh=float(body.limit_kmh)
        )
    )
    return SpeedLimitConfigResponse.from_dto(dto)


@speed_limit_router.patch("/{speed_limit_config_id}", response_model=SpeedLimitConfigResponse)
async def update_speed_limit_config(
    speed_limit_config_id: uuid.UUID, body: UpdateSpeedLimitConfigRequest,
    actor: AuthenticatedActor = Depends(require_permission("tracking.speed_limit_config.edit")),
) -> SpeedLimitConfigResponse:
    handler = UpdateSpeedLimitConfigHandler()
    status = SpeedLimitConfigStatus(body.status) if body.status is not None else None
    limit_kmh = float(body.limit_kmh) if body.limit_kmh is not None else None
    dto = await handler.handle(
        UpdateSpeedLimitConfigCommand(
            actor=actor, speed_limit_config_id=speed_limit_config_id, limit_kmh=limit_kmh, status=status
        )
    )
    return SpeedLimitConfigResponse.from_dto(dto)
