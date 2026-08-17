from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.correction_letter_dto import CorrectionLetterDTO


class CorrectionLetterResponse(BaseModel):
    id: uuid.UUID
    sequence_number: int
    correction_text: str
    xml_file_id: uuid.UUID | None
    sent_at: datetime

    @staticmethod
    def from_dto(dto: CorrectionLetterDTO) -> "CorrectionLetterResponse":
        return CorrectionLetterResponse(
            id=dto.id, sequence_number=dto.numero_sequencial, correction_text=dto.texto_correcao,
            xml_file_id=dto.xml_arquivo_id, sent_at=dto.data_hora_envio,
        )


class CreateCorrectionLetterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correction_text: str
