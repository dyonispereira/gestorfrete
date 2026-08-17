from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.fleet.application.dtos.implement_dto import ImplementDTO


class ImplementResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    plate: str
    renavam: str
    body_type: str
    category_id: uuid.UUID
    load_capacity: Decimal
    availability_status: str

    @staticmethod
    def from_dto(dto: ImplementDTO) -> "ImplementResponse":
        return ImplementResponse(
            id=dto.id, codigo=dto.codigo, plate=dto.placa, renavam=dto.renavam, body_type=dto.body_type,
            category_id=dto.category_id, load_capacity=dto.load_capacity, availability_status=dto.availability_status,
        )


class CreateImplementRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    plate: str
    renavam: str
    body_type: str
    category_id: uuid.UUID
    load_capacity: Decimal


class UpdateImplementRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    body_type: str | None = None
    load_capacity: Decimal | None = None
    availability_status: str | None = None
