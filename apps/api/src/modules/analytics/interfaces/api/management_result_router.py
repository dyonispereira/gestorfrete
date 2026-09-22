from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.analytics.application.queries.get_client_management_result_detail import (
    GetClientManagementResultDetailHandler,
    GetClientManagementResultDetailQuery,
)
from modules.analytics.application.queries.get_driver_management_result_detail import (
    GetDriverManagementResultDetailHandler,
    GetDriverManagementResultDetailQuery,
)
from modules.analytics.application.queries.get_management_result_overview import (
    GetManagementResultOverviewHandler,
    GetManagementResultOverviewQuery,
)
from modules.analytics.application.queries.get_vehicle_management_result_detail import (
    GetVehicleManagementResultDetailHandler,
    GetVehicleManagementResultDetailQuery,
)
from modules.analytics.application.queries.list_client_management_results import (
    ListClientManagementResultsHandler,
    ListClientManagementResultsQuery,
)
from modules.analytics.application.queries.list_driver_management_results import (
    ListDriverManagementResultsHandler,
    ListDriverManagementResultsQuery,
)
from modules.analytics.application.queries.list_trip_management_results import (
    ListTripManagementResultsHandler,
    ListTripManagementResultsQuery,
)
from modules.analytics.application.queries.list_vehicle_management_results import (
    ListVehicleManagementResultsHandler,
    ListVehicleManagementResultsQuery,
)
from modules.analytics.interfaces.schemas.management_result_schemas import (
    ClientResultDetailResponse,
    ClientResultResponse,
    DriverResultDetailResponse,
    DriverResultResponse,
    OverviewResultResponse,
    TripResultResponse,
    VehicleResultDetailResponse,
    VehicleResultResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/analytics/resultado-gerencial", tags=["Management Results"])


@router.get("/visao-geral", response_model=OverviewResultResponse)
async def get_overview(
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.executive_dashboard.view")),
) -> OverviewResultResponse:
    handler = GetManagementResultOverviewHandler(get_session_factory())
    dto = await handler.handle(GetManagementResultOverviewQuery(actor=actor, date_from=date_from, date_to=date_to))
    return OverviewResultResponse.from_dto(dto)


@router.get("/viagens")
async def list_trips(
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    client_id: uuid.UUID | None = None,
    vehicle_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("analytics.freight_report.view")),
) -> dict[str, Any]:
    handler = ListTripManagementResultsHandler(get_session_factory())
    result = await handler.handle(
        ListTripManagementResultsQuery(
            actor=actor, date_from=date_from, date_to=date_to, client_id=client_id, vehicle_id=vehicle_id,
            driver_id=driver_id, page=page, limit=limit,
        )
    )
    return {
        "data": [TripResultResponse.from_dto(t) for t in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/veiculos", response_model=list[VehicleResultResponse])
async def list_vehicles(
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.maintenance_report.view")),
) -> list[VehicleResultResponse]:
    handler = ListVehicleManagementResultsHandler(get_session_factory())
    results = await handler.handle(ListVehicleManagementResultsQuery(actor=actor, date_from=date_from, date_to=date_to))
    return [VehicleResultResponse.from_dto(r) for r in results]


@router.get("/veiculos/{vehicle_id}", response_model=VehicleResultDetailResponse)
async def get_vehicle_detail(
    vehicle_id: uuid.UUID,
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.maintenance_report.view")),
) -> VehicleResultDetailResponse:
    handler = GetVehicleManagementResultDetailHandler(get_session_factory())
    dto = await handler.handle(
        GetVehicleManagementResultDetailQuery(actor=actor, vehicle_id=vehicle_id, date_from=date_from, date_to=date_to)
    )
    return VehicleResultDetailResponse.from_dto(dto)


@router.get("/clientes", response_model=list[ClientResultResponse])
async def list_clients(
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.financial_report.view")),
) -> list[ClientResultResponse]:
    handler = ListClientManagementResultsHandler(get_session_factory())
    results = await handler.handle(ListClientManagementResultsQuery(actor=actor, date_from=date_from, date_to=date_to))
    return [ClientResultResponse.from_dto(r) for r in results]


@router.get("/clientes/{client_id}", response_model=ClientResultDetailResponse)
async def get_client_detail(
    client_id: uuid.UUID,
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.financial_report.view")),
) -> ClientResultDetailResponse:
    handler = GetClientManagementResultDetailHandler(get_session_factory())
    dto = await handler.handle(
        GetClientManagementResultDetailQuery(actor=actor, client_id=client_id, date_from=date_from, date_to=date_to)
    )
    return ClientResultDetailResponse.from_dto(dto)


@router.get("/motoristas", response_model=list[DriverResultResponse])
async def list_drivers(
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.driver_report.view")),
) -> list[DriverResultResponse]:
    handler = ListDriverManagementResultsHandler(get_session_factory())
    results = await handler.handle(ListDriverManagementResultsQuery(actor=actor, date_from=date_from, date_to=date_to))
    return [DriverResultResponse.from_dto(r) for r in results]


@router.get("/motoristas/{driver_id}", response_model=DriverResultDetailResponse)
async def get_driver_detail(
    driver_id: uuid.UUID,
    date_from: date | None = Query(default=None, alias="data_programada__gte"),
    date_to: date | None = Query(default=None, alias="data_programada__lte"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.driver_report.view")),
) -> DriverResultDetailResponse:
    handler = GetDriverManagementResultDetailHandler(get_session_factory())
    dto = await handler.handle(
        GetDriverManagementResultDetailQuery(actor=actor, driver_id=driver_id, date_from=date_from, date_to=date_to)
    )
    return DriverResultDetailResponse.from_dto(dto)
