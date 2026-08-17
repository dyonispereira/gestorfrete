from __future__ import annotations

import uuid
from decimal import Decimal

from core.exceptions.base import ConflictError
from modules.ai.domain.value_objects.anomaly_status import AnomalyStatus
from shared_kernel.domain.base_entity import BaseEntity


class AIAnomaly(BaseEntity[uuid.UUID]):
    """`anomalias_detectadas` — desvio estatístico detectado num fluxo contínuo de leituras
    (Posição/Telemetria/Medição de Pneu), distinta de Classificação por não ser um rótulo atribuído
    sob demanda. Nunca altera nem substitui a leitura de origem (D164)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        inferencia_ia_id: uuid.UUID,
        leitura_origem_tipo: str,
        leitura_origem_id: uuid.UUID,
        nivel_confianca: Decimal,
        status: AnomalyStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.inferencia_ia_id = inferencia_ia_id
        self.leitura_origem_tipo = leitura_origem_tipo
        self.leitura_origem_id = leitura_origem_id
        self.nivel_confianca = nivel_confianca
        self.status = status

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, inferencia_ia_id: uuid.UUID, leitura_origem_tipo: str,
        leitura_origem_id: uuid.UUID, nivel_confianca: Decimal,
    ) -> "AIAnomaly":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, inferencia_ia_id=inferencia_ia_id,
            leitura_origem_tipo=leitura_origem_tipo, leitura_origem_id=leitura_origem_id,
            nivel_confianca=nivel_confianca, status=AnomalyStatus.ABERTA,
        )

    def review(self, *, resolution: AnomalyStatus) -> None:
        """`075` — única transição real: `ABERTA → INVESTIGADA` ou `ABERTA → DESCARTADA`."""

        if self.status != AnomalyStatus.ABERTA:
            raise ConflictError("AI_ANOMALY_INVALID_TRANSITION", "Anomalia já foi revisada.")
        self.status = resolution
