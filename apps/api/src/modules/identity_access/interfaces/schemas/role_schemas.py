from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from modules.identity_access.application.dtos.role_dto import RoleDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class RoleResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nome: str
    descricao: str | None
    permissions: list[str]
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: RoleDTO) -> "RoleResponse":
        return RoleResponse(
            id=dto.id,
            codigo=dto.codigo,
            nome=dto.nome,
            descricao=dto.descricao,
            permissions=dto.permission_codes,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateRoleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    descricao: str | None = None
    permissions: list[str] = Field(default_factory=list)


class UpdateRoleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    descricao: str | None = None
    permissions: list[str] | None = None
