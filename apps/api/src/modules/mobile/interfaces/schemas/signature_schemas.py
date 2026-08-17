from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.mobile.application.dtos.digital_signature_dto import DigitalSignatureDTO


class DigitalSignatureResponse(BaseModel):
    id: uuid.UUID
    document_type: str
    document_id: uuid.UUID
    signatory_role: str
    signatory_name: str | None
    file_id: uuid.UUID
    captured_at: datetime
    received_at: datetime

    @staticmethod
    def from_dto(dto: DigitalSignatureDTO) -> "DigitalSignatureResponse":
        return DigitalSignatureResponse(
            id=dto.id, document_type=dto.documento_tipo, document_id=dto.documento_id,
            signatory_role=dto.papel_signatario, signatory_name=dto.nome_signatario_informado,
            file_id=dto.arquivo_id, captured_at=dto.data_hora_captura, received_at=dto.data_hora_recebimento,
        )
