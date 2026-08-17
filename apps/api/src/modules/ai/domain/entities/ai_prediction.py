from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from modules.ai.domain.value_objects.prediction_status import PredictionStatus
from shared_kernel.domain.base_entity import BaseEntity


class AIPrediction(BaseEntity[uuid.UUID]):
    """`predicoes_ia` (D163) — histórica (D037), nunca editada após gerada. `status` físico
    permanece `ATUAL` para sempre nesta fundação (sem job de expiração, D425) — o status EFETIVO é
    sempre recalculado pela Application na leitura, comparando `now()` a `data_hora_validade_fim`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        inferencia_ia_id: uuid.UUID,
        categoria: str,
        entidade_alvo_tipo: str,
        entidade_alvo_id: uuid.UUID,
        valor_previsto: Decimal,
        nivel_confianca: Decimal,
        data_hora_validade_fim: datetime,
        status: PredictionStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.inferencia_ia_id = inferencia_ia_id
        self.categoria = categoria
        self.entidade_alvo_tipo = entidade_alvo_tipo
        self.entidade_alvo_id = entidade_alvo_id
        self.valor_previsto = valor_previsto
        self.nivel_confianca = nivel_confianca
        self.data_hora_validade_fim = data_hora_validade_fim
        self.status = status

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, inferencia_ia_id: uuid.UUID, categoria: str,
        entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID, valor_previsto: Decimal,
        nivel_confianca: Decimal, data_hora_validade_fim: datetime,
    ) -> "AIPrediction":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, inferencia_ia_id=inferencia_ia_id, categoria=categoria,
            entidade_alvo_tipo=entidade_alvo_tipo, entidade_alvo_id=entidade_alvo_id,
            valor_previsto=valor_previsto, nivel_confianca=nivel_confianca,
            data_hora_validade_fim=data_hora_validade_fim, status=PredictionStatus.ATUAL,
        )

    def effective_status(self, *, now: datetime) -> PredictionStatus:
        """D312/D425 — nunca confia cegamente no `status` gravado; recalcula a cada leitura."""

        if now > self.data_hora_validade_fim:
            return PredictionStatus.EXPIRADA
        return self.status
