from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.maintenance.application.dtos.supplier_dto import SupplierDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class SupplierResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    razao_social: str
    cnpj: str
    telefone: str | None
    category: str | None
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: SupplierDTO) -> "SupplierResponse":
        return SupplierResponse(
            id=dto.id,
            codigo=dto.codigo,
            razao_social=dto.razao_social,
            cnpj=dto.cnpj,
            telefone=dto.telefone,
            category=dto.category,
            status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateSupplierRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    razao_social: str
    cnpj: str
    telefone: str | None = None
    category: str | None = None


class UpdateSupplierRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    razao_social: str | None = None
    telefone: str | None = None
    category: str | None = None
