from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tracking.domain.entities.tracking_equipment import TrackingEquipment


@dataclass(frozen=True)
class TrackingEquipmentDTO:
    id: uuid.UUID
    provedor_rastreamento_id: uuid.UUID
    identificador_serial: str
    tipo_equipamento: str
    veiculo_tracionador_id: uuid.UUID | None
    data_inicio_vigencia: datetime | None
    data_fim_vigencia: datetime | None
    status: str

    @staticmethod
    def from_entity(entity: TrackingEquipment) -> "TrackingEquipmentDTO":
        return TrackingEquipmentDTO(
            id=entity.id, provedor_rastreamento_id=entity.provedor_rastreamento_id,
            identificador_serial=entity.identificador_serial, tipo_equipamento=entity.tipo_equipamento.value,
            veiculo_tracionador_id=entity.veiculo_tracionador_id,
            data_inicio_vigencia=entity.data_inicio_vigencia, data_fim_vigencia=entity.data_fim_vigencia,
            status=entity.status.value,
        )
