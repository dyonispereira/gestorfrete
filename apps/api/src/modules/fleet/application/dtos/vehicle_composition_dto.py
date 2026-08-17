from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.entities.vehicle_composition import VehicleComposition


@dataclass(frozen=True)
class VehicleCompositionImplementDTO:
    implement_id: uuid.UUID
    order: int


@dataclass(frozen=True)
class VehicleCompositionDTO:
    id: uuid.UUID
    tractor_unit_id: uuid.UUID
    combination_type: str
    total_axles: int
    status: str
    implements: list[VehicleCompositionImplementDTO]
    starts_at: datetime
    ends_at: datetime | None

    @staticmethod
    def from_entity(composition: VehicleComposition) -> "VehicleCompositionDTO":
        return VehicleCompositionDTO(
            id=composition.id,
            tractor_unit_id=composition.veiculo_tracionador_id,
            combination_type=composition.tipo_combinacao.value,
            total_axles=composition.eixos_total,
            status=composition.status.value,
            implements=[
                VehicleCompositionImplementDTO(implement_id=implement_id, order=order)
                for implement_id, order in composition.implementos
            ],
            starts_at=composition.data_inicio_vigencia,
            ends_at=composition.data_fim_vigencia,
        )
