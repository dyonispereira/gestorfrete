from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.analytics.domain.entities.consolidated_indicator import ConsolidatedIndicator


@dataclass(frozen=True)
class ConsolidatedIndicatorDTO:
    id: uuid.UUID
    metric_id: uuid.UUID
    metric_version: int
    dimension_type: str
    dimension_id: uuid.UUID
    reference_period: str
    value: Decimal
    calculated_at: datetime
    status: str

    @staticmethod
    def from_entity(indicator: ConsolidatedIndicator) -> "ConsolidatedIndicatorDTO":
        return ConsolidatedIndicatorDTO(
            id=indicator.id, metric_id=indicator.metrica_id, metric_version=indicator.metrica_versao,
            dimension_type=indicator.dimensao_tipo, dimension_id=indicator.dimensao_id,
            reference_period=indicator.periodo_referencia, value=indicator.valor,
            calculated_at=indicator.data_hora_calculo, status=indicator.status.value,
        )
