from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.documents.domain.entities.fiscal_event import FiscalEvent


@dataclass(frozen=True)
class FiscalEventDTO:
    id: uuid.UUID
    documento_tipo: str
    documento_id: uuid.UUID
    tipo_evento: str
    payload_arquivo_id: uuid.UUID
    protocolo_externo: str | None
    data_hora_inicio: datetime
    data_hora_fim: datetime | None
    duracao_ms: int | None
    numero_tentativa: int
    resultado: str | None
    origem: str

    @staticmethod
    def from_entity(entity: FiscalEvent) -> "FiscalEventDTO":
        return FiscalEventDTO(
            id=entity.id, documento_tipo=entity.documento_tipo.value, documento_id=entity.documento_id,
            tipo_evento=entity.tipo_evento.value, payload_arquivo_id=entity.payload_arquivo_id,
            protocolo_externo=entity.protocolo_externo, data_hora_inicio=entity.data_hora_inicio,
            data_hora_fim=entity.data_hora_fim, duracao_ms=entity.duracao_ms,
            numero_tentativa=entity.numero_tentativa,
            resultado=entity.resultado.value if entity.resultado is not None else None, origem=entity.origem,
        )
