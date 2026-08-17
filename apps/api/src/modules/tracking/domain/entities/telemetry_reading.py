from __future__ import annotations

import uuid
from datetime import datetime

from modules.tracking.domain.value_objects.sensor_type import SensorType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class TelemetryReading(BaseAggregateRoot[uuid.UUID]):
    """`leituras_telemetria` — Time Series (D191), EAV (D120): uma linha por sensor por instante,
    nunca uma coluna por sensor. Imutável (D121) — sem método de mutação."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        equipamento_rastreamento_id: uuid.UUID,
        posicao_veiculo_id: uuid.UUID | None,
        tipo_sensor: SensorType,
        valor: float,
        unidade: str,
        capturado_em: datetime,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.equipamento_rastreamento_id = equipamento_rastreamento_id
        self.posicao_veiculo_id = posicao_veiculo_id
        self.tipo_sensor = tipo_sensor
        self.valor = valor
        self.unidade = unidade
        self.capturado_em = capturado_em
        self.recebido_em = recebido_em
        self.processado_em = processado_em

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        equipamento_rastreamento_id: uuid.UUID,
        posicao_veiculo_id: uuid.UUID | None = None,
        tipo_sensor: SensorType,
        valor: float,
        unidade: str,
        capturado_em: datetime,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> "TelemetryReading":
        return cls(
            id=uuid.uuid4(), veiculo_tracionador_id=veiculo_tracionador_id,
            equipamento_rastreamento_id=equipamento_rastreamento_id, posicao_veiculo_id=posicao_veiculo_id,
            tipo_sensor=tipo_sensor, valor=valor, unidade=unidade, capturado_em=capturado_em,
            recebido_em=recebido_em, processado_em=processado_em,
        )
