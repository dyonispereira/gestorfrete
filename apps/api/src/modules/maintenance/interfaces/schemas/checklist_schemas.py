from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class ChecklistResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    type: str
    reference_type: str
    reference_id: uuid.UUID
    tractor_unit_id: uuid.UUID
    driver_id: uuid.UUID | None
    items: list[dict[str, Any]]
    status: str
    rejected_checklist_id: uuid.UUID | None
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: ChecklistDTO) -> "ChecklistResponse":
        return ChecklistResponse(
            id=dto.id, codigo=dto.codigo, type=dto.tipo, reference_type=dto.referencia_tipo,
            reference_id=dto.referencia_id, tractor_unit_id=dto.veiculo_tracionador_id, driver_id=dto.motorista_id,
            items=dto.itens, status=dto.status, rejected_checklist_id=dto.checklist_reprovado_id,
            audit=AuditMetadataResponse(
                created_at=dto.criado_em, created_by=None, updated_at=dto.atualizado_em, updated_by=None
            ),
        )


class CreateChecklistRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    reference_type: str
    reference_id: uuid.UUID


class ChecklistItemPayload(BaseModel):
    descricao: str
    critico: bool
    resposta: bool


class SubmitChecklistRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    itens: list[ChecklistItemPayload]


class RejectChecklistRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    observacao: str


class ChecklistStatusHistoryEntryResponse(BaseModel):
    """Mesmo formato de `documents.status_history_schemas.StatusHistoryEntryResponse` (D284-style)."""

    id: uuid.UUID
    status: str
    user_id: uuid.UUID | None
    origin: str
    notes: str | None
    occurred_at: datetime
