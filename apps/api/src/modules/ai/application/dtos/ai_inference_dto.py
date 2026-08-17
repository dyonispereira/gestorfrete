from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from modules.ai.domain.entities.ai_inference import AIInference


@dataclass(frozen=True)
class AIInferenceDTO:
    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    confidence_level: Decimal | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    cost: Decimal | None
    attempt_number: int
    origin: str
    status: str

    @staticmethod
    def from_entity(inference: AIInference, *, has_cost_permission: bool) -> "AIInferenceDTO":
        return AIInferenceDTO(
            id=inference.id, model_id=inference.modelo_ia_id, model_version=inference.modelo_ia_versao,
            input=inference.entrada, output=inference.saida, confidence_level=inference.nivel_confianca,
            started_at=inference.data_hora_inicio, finished_at=inference.data_hora_fim,
            duration_ms=inference.duracao_ms, cost=inference.custo if has_cost_permission else None,
            attempt_number=inference.numero_tentativa, origin=inference.origem.value,
            status=inference.status.value,
        )
