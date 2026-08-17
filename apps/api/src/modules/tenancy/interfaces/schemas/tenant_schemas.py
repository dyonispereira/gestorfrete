from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.tenancy.application.dtos.tenant_dto import TenantDTO


class AuditMetadataResponse(BaseModel):
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None


class TenantResponse(BaseModel):
    """Espelha `components/schemas.md#Tenant` — `status` é sempre `readOnly` (nunca aparece em
    `UpdateTenantRequest`)."""

    model_config = ConfigDict(extra="ignore")

    id: uuid.UUID
    codigo: str
    razao_social: str
    cnpj: str
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: TenantDTO) -> "TenantResponse":
        return TenantResponse(
            id=dto.id,
            codigo=dto.codigo,
            razao_social=dto.razao_social,
            cnpj=dto.cnpj,
            status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at,
                created_by=dto.created_by,
                updated_at=dto.updated_at,
                updated_by=dto.updated_by,
            ),
        )


class UpdateTenantRequest(BaseModel):
    """`PATCH` é sempre parcial (`002-tenants.md`) — `extra="ignore"` garante que um `tenant_id`
    (ou qualquer outro campo não declarado) enviado por engano no corpo é silenciosamente
    descartado, nunca lido (D208/D338 reforçados até a camada de validação de schema)."""

    model_config = ConfigDict(extra="ignore")

    razao_social: str | None = None
    cnpj: str | None = None
