from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.fleet.domain.entities.implement import Implement


@dataclass(frozen=True)
class ImplementDTO:
    id: uuid.UUID
    codigo: str
    placa: str
    renavam: str
    body_type: str
    category_id: uuid.UUID
    load_capacity: Decimal
    availability_status: str

    @staticmethod
    def from_entity(implement: Implement) -> "ImplementDTO":
        return ImplementDTO(
            id=implement.id,
            codigo=implement.codigo,
            placa=implement.placa,
            renavam=implement.renavam,
            body_type=implement.tipo_carroceria.value,
            category_id=implement.categoria_veiculo_id,
            load_capacity=implement.capacidade_carga,
            availability_status=implement.status_disponibilidade.value,
        )
