from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tracking.domain.entities.telemetry_reading import TelemetryReading


@dataclass(frozen=True)
class TelemetryReadingDTO:
    id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    equipamento_rastreamento_id: uuid.UUID
    posicao_veiculo_id: uuid.UUID | None
    tipo_sensor: str
    valor: float
    unidade: str
    capturado_em: datetime
    recebido_em: datetime
    processado_em: datetime

    @staticmethod
    def from_entity(entity: TelemetryReading) -> "TelemetryReadingDTO":
        return TelemetryReadingDTO(
            id=entity.id, veiculo_tracionador_id=entity.veiculo_tracionador_id,
            equipamento_rastreamento_id=entity.equipamento_rastreamento_id,
            posicao_veiculo_id=entity.posicao_veiculo_id, tipo_sensor=entity.tipo_sensor.value,
            valor=entity.valor, unidade=entity.unidade, capturado_em=entity.capturado_em,
            recebido_em=entity.recebido_em, processado_em=entity.processado_em,
        )
