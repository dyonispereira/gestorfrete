from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from shared_kernel.domain.base_entity import BaseEntity


class OdometerReading(BaseEntity[uuid.UUID]):
    """Não-Aggregate-Root, Time Series/Histórica (D037/D050) — imutável, sem `update`
    (`ODOMETER_IMPLEMENTATION.md`, D246)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        valor_km: Decimal,
        origem: OdometerOrigin,
        viagem_id: uuid.UUID | None,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.valor_km = valor_km
        self.origem = origem
        self.viagem_id = viagem_id
        self.data_hora = data_hora

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        valor_km: Decimal,
        origem: OdometerOrigin,
        viagem_id: uuid.UUID | None,
        now: datetime,
    ) -> "OdometerReading":
        return cls(
            id=uuid.uuid4(),
            veiculo_tracionador_id=veiculo_tracionador_id,
            valor_km=valor_km,
            origem=origem,
            viagem_id=viagem_id,
            data_hora=now,
        )
