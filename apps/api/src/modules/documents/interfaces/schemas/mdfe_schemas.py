from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.mdfe_dto import MdfeDTO


class MdfeResponse(BaseModel):
    """D400 — sem `audit`: `mdfes` não tem nenhuma coluna de timestamp na DDL congelada."""

    id: uuid.UUID
    trip_id: uuid.UUID
    number: str
    series: str
    access_key: str | None
    status: str
    cte_ids: list[uuid.UUID]
    xml_file_id: uuid.UUID | None
    sefaz_protocol: str | None
    closed_at: datetime | None

    @staticmethod
    def from_dto(dto: MdfeDTO) -> "MdfeResponse":
        return MdfeResponse(
            id=dto.id, trip_id=dto.viagem_id, number=dto.numero, series=dto.serie,
            access_key=dto.chave_acesso, status=dto.status, cte_ids=dto.cte_ids,
            xml_file_id=dto.xml_arquivo_id, sefaz_protocol=dto.protocolo_sefaz,
            closed_at=dto.data_hora_encerramento,
        )


class CreateMdfeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trip_id: uuid.UUID
    cte_ids: list[uuid.UUID]


class CancelMdfeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str
