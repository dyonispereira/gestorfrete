from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from modules.mobile.domain.entities.sync_record import SyncRecord


@dataclass(frozen=True)
class SyncItemResultDTO:
    local_id: str
    result: str
    server_id: uuid.UUID | None = None
    error_code: str | None = None
    error_message: str | None = None
    conflict_current_state: dict[str, Any] | None = None
    conflict_reason: str | None = None


@dataclass(frozen=True)
class SyncBatchResultDTO:
    sync_record_id: uuid.UUID
    results: list[SyncItemResultDTO]


@dataclass(frozen=True)
class SyncRecordDTO:
    id: uuid.UUID
    sessao_mobile_id: uuid.UUID
    data_hora_inicio: datetime
    data_hora_fim: datetime
    duracao_ms: int | None
    quantidade_comandos: int
    quantidade_sucesso: int
    quantidade_falha: int

    @staticmethod
    def from_entity(entity: SyncRecord, duracao_ms: int | None) -> "SyncRecordDTO":
        return SyncRecordDTO(
            id=entity.id, sessao_mobile_id=entity.sessao_mobile_id, data_hora_inicio=entity.data_hora_inicio,
            data_hora_fim=entity.data_hora_fim, duracao_ms=duracao_ms,
            quantidade_comandos=entity.quantidade_comandos, quantidade_sucesso=entity.quantidade_sucesso,
            quantidade_falha=entity.quantidade_falha,
        )
