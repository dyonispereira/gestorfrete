from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.documents.domain.entities.correction_letter import CorrectionLetter


@dataclass(frozen=True)
class CorrectionLetterDTO:
    id: uuid.UUID
    cte_id: uuid.UUID
    numero_sequencial: int
    texto_correcao: str
    xml_arquivo_id: uuid.UUID | None
    data_hora_envio: datetime

    @staticmethod
    def from_entity(entity: CorrectionLetter) -> "CorrectionLetterDTO":
        return CorrectionLetterDTO(
            id=entity.id, cte_id=entity.cte_id, numero_sequencial=entity.numero_sequencial,
            texto_correcao=entity.texto_correcao, xml_arquivo_id=entity.xml_arquivo_id,
            data_hora_envio=entity.data_hora_envio,
        )
