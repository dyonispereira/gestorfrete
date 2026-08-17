from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tracking.domain.entities.tracking_event import TrackingEvent


@dataclass(frozen=True)
class TrackingEventDTO:
    id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    tipo: str
    posicao_veiculo_id: uuid.UUID | None
    cerca_eletronica_id: uuid.UUID | None
    configuracao_limite_velocidade_id: uuid.UUID | None
    valor_detectado: float | None
    severidade: str
    data_hora: datetime

    @staticmethod
    def from_entity(entity: TrackingEvent) -> "TrackingEventDTO":
        return TrackingEventDTO(
            id=entity.id, veiculo_tracionador_id=entity.veiculo_tracionador_id, tipo=entity.tipo.value,
            posicao_veiculo_id=entity.posicao_veiculo_id, cerca_eletronica_id=entity.cerca_eletronica_id,
            configuracao_limite_velocidade_id=entity.configuracao_limite_velocidade_id,
            valor_detectado=entity.valor_detectado, severidade=entity.severidade.value, data_hora=entity.data_hora,
        )
