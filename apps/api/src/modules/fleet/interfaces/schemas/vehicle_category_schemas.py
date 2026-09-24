from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.fleet.application.dtos.vehicle_category_dto import VehicleCategoryDTO


class VehicleCategoryResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nome: str
    status: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_dto(dto: VehicleCategoryDTO) -> "VehicleCategoryResponse":
        return VehicleCategoryResponse(
            id=dto.id, codigo=dto.codigo, nome=dto.nome, status=dto.status,
            created_at=dto.created_at, updated_at=dto.updated_at,
        )


class CreateVehicleCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str


class UpdateVehicleCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    status: str | None = None
