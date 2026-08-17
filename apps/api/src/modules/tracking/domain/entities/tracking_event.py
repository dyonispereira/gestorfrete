from __future__ import annotations

import uuid
from datetime import datetime

from modules.tracking.domain.value_objects.tracking_event_severity import TrackingEventSeverity
from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class TrackingEvent(BaseAggregateRoot[uuid.UUID]):
    """`eventos_rastreamento` — derivado (D119/D288), nunca substitui a leitura bruta que o originou;
    `position_id`/`geofence_id`/`speed_limit_config_id` são sempre referências, nunca cópia de dado.
    Imutável (D037/D121) — sem método de mutação."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo: TrackingEventType,
        posicao_veiculo_id: uuid.UUID | None,
        cerca_eletronica_id: uuid.UUID | None,
        configuracao_limite_velocidade_id: uuid.UUID | None,
        valor_detectado: float | None,
        severidade: TrackingEventSeverity,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.tipo = tipo
        self.posicao_veiculo_id = posicao_veiculo_id
        self.cerca_eletronica_id = cerca_eletronica_id
        self.configuracao_limite_velocidade_id = configuracao_limite_velocidade_id
        self.valor_detectado = valor_detectado
        self.severidade = severidade
        self.data_hora = data_hora

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo: TrackingEventType,
        severidade: TrackingEventSeverity,
        posicao_veiculo_id: uuid.UUID | None = None,
        cerca_eletronica_id: uuid.UUID | None = None,
        configuracao_limite_velocidade_id: uuid.UUID | None = None,
        valor_detectado: float | None = None,
        data_hora: datetime,
    ) -> "TrackingEvent":
        return cls(
            id=uuid.uuid4(), veiculo_tracionador_id=veiculo_tracionador_id, tipo=tipo,
            posicao_veiculo_id=posicao_veiculo_id, cerca_eletronica_id=cerca_eletronica_id,
            configuracao_limite_velocidade_id=configuracao_limite_velocidade_id,
            valor_detectado=valor_detectado, severidade=severidade, data_hora=data_hora,
        )
