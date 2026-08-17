from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.ciot_dto import CiotDTO


class CiotResponse(BaseModel):
    """D400 — sem `audit`: `ciots` não tem nenhuma coluna de timestamp na DDL congelada."""

    id: uuid.UUID
    trip_id: uuid.UUID
    driver_id: uuid.UUID
    ciot_code: str | None
    status: str
    antt_protocol: str | None
    registered_at: datetime | None

    @staticmethod
    def from_dto(dto: CiotDTO) -> "CiotResponse":
        return CiotResponse(
            id=dto.id, trip_id=dto.viagem_id, driver_id=dto.motorista_id, ciot_code=dto.codigo_ciot,
            status=dto.status, antt_protocol=dto.protocolo_antt, registered_at=dto.data_hora_registro,
        )


class CreateCiotRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trip_id: uuid.UUID
    driver_id: uuid.UUID


class CancelCiotRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str
