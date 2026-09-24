from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.entities.vehicle_category import VehicleCategory


@dataclass(frozen=True)
class VehicleCategoryDTO:
    id: uuid.UUID
    codigo: str
    nome: str
    status: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_entity(category: VehicleCategory) -> "VehicleCategoryDTO":
        return VehicleCategoryDTO(
            id=category.id, codigo=category.codigo, nome=category.nome, status=category.status.value,
            created_at=category.created_at, updated_at=category.updated_at,
        )
