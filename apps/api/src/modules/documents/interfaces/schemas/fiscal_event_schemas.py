from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from modules.documents.application.dtos.fiscal_event_dto import FiscalEventDTO


class FiscalEventResponse(BaseModel):
    """D277 — somente leitura para usuários, todo campo `readOnly` no contrato."""

    id: uuid.UUID
    document_type: str
    document_id: uuid.UUID
    event_type: str
    payload_file_id: uuid.UUID
    external_protocol: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    attempt_number: int
    result: str | None
    origin: str

    @staticmethod
    def from_dto(dto: FiscalEventDTO) -> "FiscalEventResponse":
        return FiscalEventResponse(
            id=dto.id, document_type=dto.documento_tipo, document_id=dto.documento_id,
            event_type=dto.tipo_evento, payload_file_id=dto.payload_arquivo_id,
            external_protocol=dto.protocolo_externo, started_at=dto.data_hora_inicio,
            finished_at=dto.data_hora_fim, duration_ms=dto.duracao_ms, attempt_number=dto.numero_tentativa,
            result=dto.resultado, origin=dto.origem,
        )
