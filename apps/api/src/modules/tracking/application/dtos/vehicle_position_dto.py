from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tracking.domain.entities.vehicle_position import VehiclePosition


@dataclass(frozen=True)
class VehiclePositionDTO:
    id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    equipamento_rastreamento_id: uuid.UUID
    latitude: float
    longitude: float
    origem_localizacao_id: uuid.UUID
    precisao_metros: float | None
    numero_satelites: int | None
    hdop: float | None
    nivel_confianca: float | None
    capturado_em: datetime
    recebido_em: datetime
    processado_em: datetime

    @staticmethod
    def from_entity(entity: VehiclePosition) -> "VehiclePositionDTO":
        return VehiclePositionDTO(
            id=entity.id, veiculo_tracionador_id=entity.veiculo_tracionador_id,
            equipamento_rastreamento_id=entity.equipamento_rastreamento_id,
            latitude=entity.localizacao.latitude, longitude=entity.localizacao.longitude,
            origem_localizacao_id=entity.origem_localizacao_id, precisao_metros=entity.precisao_metros,
            numero_satelites=entity.numero_satelites, hdop=entity.hdop, nivel_confianca=entity.nivel_confianca,
            capturado_em=entity.capturado_em, recebido_em=entity.recebido_em, processado_em=entity.processado_em,
        )
