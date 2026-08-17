from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from modules.ai.domain.entities.computer_vision_reading import ComputerVisionReading


@dataclass(frozen=True)
class ComputerVisionReadingDTO:
    id: uuid.UUID
    inference_id: uuid.UUID
    source_file_id: uuid.UUID
    reading_type: str
    analyzed_region: dict[str, Any] | None
    extracted_result: dict[str, Any]
    confidence_level: Decimal
    human_review_required: bool
    status: str
    confirmation_user_id: uuid.UUID | None

    @staticmethod
    def from_entity(reading: ComputerVisionReading) -> "ComputerVisionReadingDTO":
        return ComputerVisionReadingDTO(
            id=reading.id, inference_id=reading.inferencia_ia_id, source_file_id=reading.arquivo_origem_id,
            reading_type=reading.tipo_leitura.value, analyzed_region=reading.regiao_analisada,
            extracted_result=reading.resultado_extraido, confidence_level=reading.nivel_confianca,
            human_review_required=reading.revisao_humana_necessaria, status=reading.status.value,
            confirmation_user_id=reading.usuario_confirmacao_id,
        )
