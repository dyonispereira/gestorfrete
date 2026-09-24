from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.manifest_dto import CargoItemDTO, ManifestDTO


class CargoItemResponse(BaseModel):
    id: uuid.UUID
    description: str
    weight_kg: Decimal
    quantity: int

    @staticmethod
    def from_dto(dto: CargoItemDTO) -> "CargoItemResponse":
        return CargoItemResponse(id=dto.id, description=dto.descricao, weight_kg=dto.peso, quantity=dto.quantidade)


class ManifestResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    document_number: str | None
    items: list[CargoItemResponse]
    trip_operational_status: str

    @staticmethod
    def from_dto(dto: ManifestDTO) -> "ManifestResponse":
        return ManifestResponse(
            id=dto.id, trip_id=dto.viagem_id, document_number=dto.numero_documento,
            items=[CargoItemResponse.from_dto(item) for item in dto.itens],
            trip_operational_status=dto.trip_status_operacional,
        )


class CargoItemPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str
    weight_kg: Decimal
    quantity: int


class ConfirmManifestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_number: str | None = None
    items: list[CargoItemPayload]
