from __future__ import annotations

import uuid
from typing import Any

from modules.analytics.domain.value_objects.metric_dimensional_granularity import MetricDimensionalGranularity
from modules.analytics.domain.value_objects.metric_periodicity import MetricPeriodicity
from modules.analytics.domain.value_objects.metric_status import MetricStatus
from modules.analytics.domain.value_objects.metric_temporal_granularity import MetricTemporalGranularity
from shared_kernel.domain.base_entity import BaseEntity


class Metric(BaseEntity[uuid.UUID]):
    """`metricas` (D150/D155/D419) — Reference Data/catálogo. `tenant_id=None` = Platform Reference
    Data (D046), visível a todos os tenants. Nova versão é sempre uma linha física nova
    (`new_version`) — nunca um `UPDATE` de `formula` na mesma linha (D419: sem coluna de
    encadeamento entre versões na DDL congelada)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID | None,
        nome: str,
        formula: str,
        versao: int,
        granularidade_temporal: MetricTemporalGranularity,
        granularidade_dimensional: MetricDimensionalGranularity,
        unidade: str,
        origem_dados: dict[str, Any],
        periodicidade_calculo: MetricPeriodicity,
        status: MetricStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.nome = nome
        self.formula = formula
        self.versao = versao
        self.granularidade_temporal = granularidade_temporal
        self.granularidade_dimensional = granularidade_dimensional
        self.unidade = unidade
        self.origem_dados = origem_dados
        self.periodicidade_calculo = periodicidade_calculo
        self.status = status

    @classmethod
    def create(
        cls,
        *,
        tenant_id: uuid.UUID | None,
        nome: str,
        formula: str,
        granularidade_temporal: MetricTemporalGranularity,
        granularidade_dimensional: MetricDimensionalGranularity,
        unidade: str,
        origem_dados: dict[str, Any],
        periodicidade_calculo: MetricPeriodicity,
    ) -> "Metric":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, nome=nome, formula=formula, versao=1,
            granularidade_temporal=granularidade_temporal, granularidade_dimensional=granularidade_dimensional,
            unidade=unidade, origem_dados=origem_dados, periodicidade_calculo=periodicidade_calculo,
            status=MetricStatus.ATIVA,
        )

    def new_version(self, *, formula: str) -> "Metric":
        """D155/D419 — devolve uma NOVA entidade (linha física nova), nunca muta `self`. O chamador
        persiste as duas: a antiga permanece intocada para sempre (Indicadores já calculados
        continuam referenciando `metrica_id` antigo)."""

        return Metric(
            id=uuid.uuid4(), tenant_id=self.tenant_id, nome=self.nome, formula=formula, versao=self.versao + 1,
            granularidade_temporal=self.granularidade_temporal,
            granularidade_dimensional=self.granularidade_dimensional, unidade=self.unidade,
            origem_dados=self.origem_dados, periodicidade_calculo=self.periodicidade_calculo,
            status=self.status,
        )

    def update_fields(
        self, *, nome: str | None, unidade: str | None, origem_dados: dict[str, Any] | None,
        periodicidade_calculo: MetricPeriodicity | None, status: MetricStatus | None,
    ) -> None:
        """Campos que editam a MESMA linha, sem gerar nova versão (`062`)."""

        if nome is not None:
            self.nome = nome
        if unidade is not None:
            self.unidade = unidade
        if origem_dados is not None:
            self.origem_dados = origem_dados
        if periodicidade_calculo is not None:
            self.periodicidade_calculo = periodicidade_calculo
        if status is not None:
            self.status = status
