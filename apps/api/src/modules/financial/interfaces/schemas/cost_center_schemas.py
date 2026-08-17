from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.cost_center_dto import CostCenterDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class CostCenterResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    accounting_code: str
    nome: str
    branch_id: uuid.UUID | None
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: CostCenterDTO) -> "CostCenterResponse":
        return CostCenterResponse(
            id=dto.id,
            codigo=dto.codigo,
            accounting_code=dto.codigo_contabil,
            nome=dto.nome,
            branch_id=dto.filial_id,
            status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateCostCenterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accounting_code: str
    nome: str
    branch_id: uuid.UUID | None = None


class UpdateCostCenterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    branch_id: uuid.UUID | None = None
    status: str | None = None
