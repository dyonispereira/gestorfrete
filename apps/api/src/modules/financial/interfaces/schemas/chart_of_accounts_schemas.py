from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.chart_of_accounts_dto import ChartOfAccountsDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class ChartOfAccountsResponse(BaseModel):
    id: uuid.UUID
    account_code: str
    name: str
    type: str
    parent_id: uuid.UUID | None
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: ChartOfAccountsDTO) -> "ChartOfAccountsResponse":
        return ChartOfAccountsResponse(
            id=dto.id, account_code=dto.codigo_contabil, name=dto.nome, type=dto.tipo,
            parent_id=dto.categoria_pai_id, status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by,
                updated_at=dto.updated_at, updated_by=dto.updated_by,
            ),
        )


class CreateChartOfAccountsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    account_code: str
    name: str
    type: str
    parent_id: uuid.UUID | None = None


class UpdateChartOfAccountsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    parent_id: uuid.UUID | None = None
    status: str | None = None
