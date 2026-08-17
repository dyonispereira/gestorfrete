from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.cte_dto import CteDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class CteResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    number: str
    series: str
    access_key: str | None
    service_value: Decimal
    status: str
    xml_file_id: uuid.UUID | None
    sefaz_protocol: str | None
    authorized_at: datetime | None
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: CteDTO) -> "CteResponse":
        return CteResponse(
            id=dto.id, trip_id=dto.viagem_id, number=dto.numero, series=dto.serie,
            access_key=dto.chave_acesso, service_value=dto.valor_servico, status=dto.status,
            xml_file_id=dto.xml_arquivo_id, sefaz_protocol=dto.protocolo_sefaz,
            authorized_at=dto.data_hora_autorizacao,
            # D400 — `ctes` só tem `criado_em`/`atualizado_em` na DDL congelada; `created_by`/
            # `updated_by` ficam sempre `None` (nunca fabricados).
            audit=AuditMetadataResponse(
                created_at=dto.criado_em, created_by=None, updated_at=dto.atualizado_em, updated_by=None
            ),
        )


class CancelCteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str
