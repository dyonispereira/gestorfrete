from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.mobile.application.dtos.sync_dto import SyncBatchResultDTO, SyncItemResultDTO, SyncRecordDTO


class SyncQueueItemRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    local_id: str
    sequence: int
    command: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    payload: dict[str, Any]


class SyncBatchRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    commands: list[SyncQueueItemRequest]


class SyncConflictResponse(BaseModel):
    current_state: dict[str, Any] | None
    reason: str | None


class SyncErrorResponse(BaseModel):
    code: str
    message: str


class SyncItemResultResponse(BaseModel):
    local_id: str
    result: str
    server_id: uuid.UUID | None
    error: SyncErrorResponse | None
    conflict: SyncConflictResponse | None

    @staticmethod
    def from_dto(dto: SyncItemResultDTO) -> "SyncItemResultResponse":
        return SyncItemResultResponse(
            local_id=dto.local_id, result=dto.result, server_id=dto.server_id,
            error=SyncErrorResponse(code=dto.error_code, message=dto.error_message or "")
            if dto.error_code is not None else None,
            conflict=SyncConflictResponse(current_state=dto.conflict_current_state, reason=dto.conflict_reason)
            if dto.conflict_reason is not None else None,
        )


class SyncBatchResponse(BaseModel):
    sync_record_id: uuid.UUID
    results: list[SyncItemResultResponse]

    @staticmethod
    def from_dto(dto: SyncBatchResultDTO) -> "SyncBatchResponse":
        return SyncBatchResponse(
            sync_record_id=dto.sync_record_id, results=[SyncItemResultResponse.from_dto(r) for r in dto.results]
        )


class SyncRecordResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    started_at: datetime
    finished_at: datetime
    duration_ms: int | None
    command_count: int
    success_count: int
    failure_count: int

    @staticmethod
    def from_dto(dto: SyncRecordDTO) -> "SyncRecordResponse":
        return SyncRecordResponse(
            id=dto.id, session_id=dto.sessao_mobile_id, started_at=dto.data_hora_inicio,
            finished_at=dto.data_hora_fim, duration_ms=dto.duracao_ms, command_count=dto.quantidade_comandos,
            success_count=dto.quantidade_sucesso, failure_count=dto.quantidade_falha,
        )
