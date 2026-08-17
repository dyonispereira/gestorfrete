from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.fleet.application.dtos.vehicle_document_dto import VehicleDocumentDTO
from modules.fleet.application.dtos.vehicle_dto import VehicleDTO
from modules.fleet.application.dtos.vehicle_technical_sheet_dto import VehicleTechnicalSheetDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class VehicleIdentityResponse(BaseModel):
    codigo: str
    plate: str
    renavam: str


class VehicleOperationalResponse(BaseModel):
    """Sempre `readOnly` — nunca populado por `CreateVehicleHandler`/`UpdateVehicleHandler`, só
    exposto aqui como espelho do contrato (`Vehicle.operational`, `fleet-schemas.md`); fica
    ausente/nulo até a Disponibilidade real ser consultada em `/veiculos/{id}/disponibilidade`
    (D247, AVAILABILITY_IMPLEMENTATION.md) — este projeto não duplica a leitura aqui."""

    status: str | None = None
    current_driver_id: uuid.UUID | None = None
    current_implement_id: uuid.UUID | None = None
    updated_at: str | None = None


class VehicleResponse(BaseModel):
    id: uuid.UUID
    identity: VehicleIdentityResponse
    status: str
    branch_id: uuid.UUID | None
    operational: VehicleOperationalResponse
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: VehicleDTO) -> "VehicleResponse":
        return VehicleResponse(
            id=dto.id,
            identity=VehicleIdentityResponse(codigo=dto.codigo, plate=dto.placa, renavam=dto.renavam),
            status=dto.status,
            branch_id=dto.filial_id,
            operational=VehicleOperationalResponse(),
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateVehicleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    plate: str
    renavam: str
    fabricante: str
    modelo: str
    ano_fabricacao: int
    categoria_id: uuid.UUID
    branch_id: uuid.UUID | None = None


class UpdateVehicleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fabricante: str | None = None
    modelo: str | None = None
    ano_fabricacao: int | None = None
    categoria_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class VehicleTechnicalSheetResponse(BaseModel):
    id: uuid.UUID
    manufacturer: str
    model: str
    manufacture_year: int
    category_id: uuid.UUID
    chassis: str
    engine: str | None
    axles: int
    tare_weight: Decimal
    load_capacity: Decimal
    gross_vehicle_weight: Decimal
    owner_rntrc: str | None
    fuel_type: str

    @staticmethod
    def from_dto(dto: VehicleTechnicalSheetDTO) -> "VehicleTechnicalSheetResponse":
        return VehicleTechnicalSheetResponse(
            id=dto.id,
            manufacturer=dto.manufacturer,
            model=dto.model,
            manufacture_year=dto.manufacture_year,
            category_id=dto.category_id,
            chassis=dto.chassis,
            engine=dto.engine,
            axles=dto.axles,
            tare_weight=dto.tare_weight,
            load_capacity=dto.load_capacity,
            gross_vehicle_weight=dto.gross_vehicle_weight,
            owner_rntrc=dto.owner_rntrc,
            fuel_type=dto.fuel_type,
        )


class UpsertVehicleTechnicalSheetRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chassis: str | None = None
    engine: str | None = None
    axles: int | None = None
    tare_weight: Decimal | None = None
    load_capacity: Decimal | None = None
    gross_vehicle_weight: Decimal | None = None
    owner_rntrc: str | None = None
    fuel_type: str | None = None


class VehicleDocumentResponse(BaseModel):
    id: uuid.UUID
    type: str
    number: str
    expires_at: date
    status: str
    file_id: uuid.UUID | None

    @staticmethod
    def from_dto(dto: VehicleDocumentDTO) -> "VehicleDocumentResponse":
        return VehicleDocumentResponse(
            id=dto.id, type=dto.tipo, number=dto.numero, expires_at=dto.data_validade, status=dto.status, file_id=dto.arquivo_id
        )


class CreateVehicleDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    number: str
    expires_at: date
    file_id: uuid.UUID | None = None


class UpdateVehicleDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: str | None = None
    expires_at: date | None = None
    file_id: uuid.UUID | None = None
