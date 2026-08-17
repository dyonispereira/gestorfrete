from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.fleet.application.commands.create_vehicle import CreateVehicleCommand, CreateVehicleHandler
from modules.fleet.application.commands.create_vehicle_document import (
    CreateVehicleDocumentCommand,
    CreateVehicleDocumentHandler,
)
from modules.fleet.application.commands.deactivate_vehicle import DeactivateVehicleCommand, DeactivateVehicleHandler
from modules.fleet.application.commands.update_vehicle import UpdateVehicleCommand, UpdateVehicleHandler
from modules.fleet.application.commands.update_vehicle_document import (
    UpdateVehicleDocumentCommand,
    UpdateVehicleDocumentHandler,
)
from modules.fleet.application.commands.upsert_vehicle_technical_sheet import (
    UpsertVehicleTechnicalSheetCommand,
    UpsertVehicleTechnicalSheetHandler,
)
from modules.fleet.application.queries.get_vehicle import GetVehicleHandler, GetVehicleQuery
from modules.fleet.application.queries.get_vehicle_technical_sheet import (
    GetVehicleTechnicalSheetHandler,
    GetVehicleTechnicalSheetQuery,
)
from modules.fleet.application.queries.list_vehicle_documents import (
    ListVehicleDocumentsHandler,
    ListVehicleDocumentsQuery,
)
from modules.fleet.application.queries.list_vehicles import ListVehiclesHandler, ListVehiclesQuery
from modules.fleet.domain.value_objects.fuel_type import FuelType
from modules.fleet.interfaces.schemas.vehicle_schemas import (
    CreateVehicleDocumentRequest,
    CreateVehicleRequest,
    UpdateVehicleDocumentRequest,
    UpdateVehicleRequest,
    UpsertVehicleTechnicalSheetRequest,
    VehicleDocumentResponse,
    VehicleResponse,
    VehicleTechnicalSheetResponse,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/veiculos", tags=["Vehicles"])


@router.get("")
async def list_vehicles(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    placa: str | None = None,
    status: str | None = None,
    categoria_id: uuid.UUID | None = None,
    fabricante: str | None = None,
    modelo: str | None = None,
    ano: int | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.view")),
) -> dict[str, Any]:
    handler = ListVehiclesHandler(get_session_factory())
    result = await handler.handle(
        ListVehiclesQuery(
            actor=actor, page=page, limit=limit, search=search, placa=placa, status=status,
            categoria_id=categoria_id, fabricante=fabricante, modelo=modelo, ano=ano,
        )
    )
    return {
        "data": [VehicleResponse.from_dto(v) for v in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.view")),
) -> VehicleResponse:
    handler = GetVehicleHandler(get_session_factory())
    dto = await handler.handle(GetVehicleQuery(actor=actor, vehicle_id=vehicle_id))
    return VehicleResponse.from_dto(dto)


@router.post("", response_model=VehicleResponse, status_code=201)
async def create_vehicle(
    body: CreateVehicleRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.create")),
) -> VehicleResponse:
    handler = CreateVehicleHandler()
    dto = await handler.handle(
        CreateVehicleCommand(
            actor=actor, placa=body.plate, renavam=body.renavam, fabricante=body.fabricante, modelo=body.modelo,
            ano_fabricacao=body.ano_fabricacao, categoria_id=body.categoria_id, filial_id=body.branch_id,
        )
    )
    return VehicleResponse.from_dto(dto)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    body: UpdateVehicleRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.edit")),
) -> VehicleResponse:
    handler = UpdateVehicleHandler()
    dto = await handler.handle(
        UpdateVehicleCommand(
            actor=actor, vehicle_id=vehicle_id, fabricante=body.fabricante, modelo=body.modelo,
            ano_fabricacao=body.ano_fabricacao, categoria_id=body.categoria_id, filial_id=body.branch_id,
        )
    )
    return VehicleResponse.from_dto(dto)


@router.delete("/{vehicle_id}", status_code=204, response_model=None)
async def deactivate_vehicle(
    vehicle_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle.delete")),
) -> None:
    handler = DeactivateVehicleHandler()
    await handler.handle(DeactivateVehicleCommand(actor=actor, vehicle_id=vehicle_id))


# --- Ficha Técnica (sub-recurso, RBAC próprio) ---


@router.get("/{vehicle_id}/technical-sheet", response_model=VehicleTechnicalSheetResponse)
async def get_vehicle_technical_sheet(
    vehicle_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_technical_sheet.view")),
) -> VehicleTechnicalSheetResponse:
    handler = GetVehicleTechnicalSheetHandler(get_session_factory())
    dto = await handler.handle(GetVehicleTechnicalSheetQuery(actor=actor, vehicle_id=vehicle_id))
    return VehicleTechnicalSheetResponse.from_dto(dto)


@router.patch("/{vehicle_id}/technical-sheet", response_model=VehicleTechnicalSheetResponse)
async def upsert_vehicle_technical_sheet(
    vehicle_id: uuid.UUID,
    body: UpsertVehicleTechnicalSheetRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_technical_sheet.edit")),
) -> VehicleTechnicalSheetResponse:
    handler = UpsertVehicleTechnicalSheetHandler()
    dto = await handler.handle(
        UpsertVehicleTechnicalSheetCommand(
            actor=actor,
            vehicle_id=vehicle_id,
            chassi=body.chassis,
            motor=body.engine,
            eixos=body.axles,
            tara=body.tare_weight,
            capacidade_carga=body.load_capacity,
            pbt=body.gross_vehicle_weight,
            rntrc_proprietario=body.owner_rntrc,
            combustivel=FuelType(body.fuel_type) if body.fuel_type else None,
        )
    )
    return VehicleTechnicalSheetResponse.from_dto(dto)


# --- Documentos do Veículo ---


@router.get("/{vehicle_id}/documentos")
async def list_vehicle_documents(
    vehicle_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_document.view")),
) -> dict[str, Any]:
    handler = ListVehicleDocumentsHandler(get_session_factory())
    result = await handler.handle(
        ListVehicleDocumentsQuery(actor=actor, vehicle_id=vehicle_id, page=page, limit=limit, tipo=type, status=status)
    )
    return {
        "data": [VehicleDocumentResponse.from_dto(d) for d in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.post("/{vehicle_id}/documentos", response_model=VehicleDocumentResponse, status_code=201)
async def create_vehicle_document(
    vehicle_id: uuid.UUID,
    body: CreateVehicleDocumentRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_document.attach")),
) -> VehicleDocumentResponse:
    handler = CreateVehicleDocumentHandler()
    dto = await handler.handle(
        CreateVehicleDocumentCommand(
            actor=actor, vehicle_id=vehicle_id, tipo=body.type, numero=body.number, data_validade=body.expires_at,
            arquivo_id=body.file_id,
        )
    )
    return VehicleDocumentResponse.from_dto(dto)


@router.patch("/{vehicle_id}/documentos/{document_id}", response_model=VehicleDocumentResponse)
async def update_vehicle_document(
    vehicle_id: uuid.UUID,
    document_id: uuid.UUID,
    body: UpdateVehicleDocumentRequest,
    actor: AuthenticatedActor = Depends(require_permission("fleet.vehicle_document.attach")),
) -> VehicleDocumentResponse:
    handler = UpdateVehicleDocumentHandler()
    dto = await handler.handle(
        UpdateVehicleDocumentCommand(
            actor=actor, vehicle_id=vehicle_id, document_id=document_id, numero=body.number,
            data_validade=body.expires_at, arquivo_id=body.file_id,
        )
    )
    return VehicleDocumentResponse.from_dto(dto)
