from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from modules.identity_access.application.dtos.employee_dto import EmployeeDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nome: str
    cargo: str
    hired_at: date | None
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: EmployeeDTO) -> "EmployeeResponse":
        return EmployeeResponse(
            id=dto.id,
            codigo=dto.codigo,
            nome=dto.nome,
            cargo=dto.cargo,
            hired_at=dto.data_admissao,
            status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateEmployeeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    cargo: str
    hired_at: date | None = None


class UpdateEmployeeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    cargo: str | None = None
    hired_at: date | None = None
