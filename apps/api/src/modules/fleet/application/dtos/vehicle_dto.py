from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.entities.vehicle import Vehicle


@dataclass(frozen=True)
class VehicleDTO:
    id: uuid.UUID
    codigo: str
    placa: str
    renavam: str
    fabricante: str
    modelo: str
    ano_fabricacao: int
    categoria_veiculo_id: uuid.UUID
    filial_id: uuid.UUID | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(vehicle: Vehicle) -> "VehicleDTO":
        return VehicleDTO(
            id=vehicle.id,
            codigo=vehicle.codigo,
            placa=vehicle.placa,
            renavam=vehicle.renavam,
            fabricante=vehicle.fabricante,
            modelo=vehicle.modelo,
            ano_fabricacao=vehicle.ano_fabricacao,
            categoria_veiculo_id=vehicle.categoria_veiculo_id,
            filial_id=vehicle.filial_id,
            status=vehicle.status.value,
            created_at=vehicle.audit.created_at,
            created_by=vehicle.audit.created_by,
            updated_at=vehicle.audit.updated_at,
            updated_by=vehicle.audit.updated_by,
        )
