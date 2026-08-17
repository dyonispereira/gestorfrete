from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.mobile.domain.entities.digital_signature import DigitalSignature


@dataclass(frozen=True)
class DigitalSignatureDTO:
    id: uuid.UUID
    documento_tipo: str
    documento_id: uuid.UUID
    papel_signatario: str
    nome_signatario_informado: str | None
    arquivo_id: uuid.UUID
    data_hora_captura: datetime
    data_hora_recebimento: datetime

    @staticmethod
    def from_entity(entity: DigitalSignature) -> "DigitalSignatureDTO":
        return DigitalSignatureDTO(
            id=entity.id, documento_tipo=entity.documento_tipo.value, documento_id=entity.documento_id,
            papel_signatario=entity.papel_signatario.value,
            nome_signatario_informado=entity.nome_signatario_informado, arquivo_id=entity.arquivo_id,
            data_hora_captura=entity.data_hora_captura, data_hora_recebimento=entity.data_hora_recebimento,
        )
