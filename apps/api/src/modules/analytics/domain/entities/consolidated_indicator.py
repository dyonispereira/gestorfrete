from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from modules.analytics.domain.value_objects.indicator_status import IndicatorStatus
from shared_kernel.domain.base_entity import BaseEntity


class ConsolidatedIndicator(BaseEntity[uuid.UUID]):
    """`indicadores_consolidados` (D090/D149/D156) — nunca criado via HTTP (`063`), só via
    `AnalyticsCalculationEngine`. `metrica_versao` é cópia fixa, nunca a fórmula em si."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        metrica_id: uuid.UUID,
        metrica_versao: int,
        dimensao_tipo: str,
        dimensao_id: uuid.UUID,
        periodo_referencia: str,
        valor: Decimal,
        data_hora_calculo: datetime,
        status: IndicatorStatus,
    ) -> None:
        super().__init__(id)
        self.metrica_id = metrica_id
        self.metrica_versao = metrica_versao
        self.dimensao_tipo = dimensao_tipo
        self.dimensao_id = dimensao_id
        self.periodo_referencia = periodo_referencia
        self.valor = valor
        self.data_hora_calculo = data_hora_calculo
        self.status = status

    @classmethod
    def calculate(
        cls, *, metrica_id: uuid.UUID, metrica_versao: int, dimensao_tipo: str, dimensao_id: uuid.UUID,
        periodo_referencia: str, valor: Decimal, now: datetime,
    ) -> "ConsolidatedIndicator":
        return cls(
            id=uuid.uuid4(), metrica_id=metrica_id, metrica_versao=metrica_versao, dimensao_tipo=dimensao_tipo,
            dimensao_id=dimensao_id, periodo_referencia=periodo_referencia, valor=valor, data_hora_calculo=now,
            status=IndicatorStatus.VALIDO,
        )

    def mark_recalculated(self) -> None:
        self.status = IndicatorStatus.RECALCULADO

    def mark_snapshotted(self) -> None:
        """D151 — a partir daqui, imutável para sempre; `AnalyticsCalculationEngine` recusa
        recalcular um indicador com este status."""

        self.status = IndicatorStatus.SNAPSHOTADO
