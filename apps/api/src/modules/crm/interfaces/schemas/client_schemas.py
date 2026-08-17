from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from modules.crm.application.dtos.client_contact_dto import ClientContactDTO
from modules.crm.application.dtos.client_dto import ClientDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class ClientResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    razao_social: str
    nome_fantasia: str | None
    document: str
    telefone: str | None
    email: str | None
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: ClientDTO) -> "ClientResponse":
        return ClientResponse(
            id=dto.id,
            codigo=dto.codigo,
            razao_social=dto.razao_social,
            nome_fantasia=dto.nome_fantasia,
            document=dto.document,
            telefone=dto.telefone,
            email=dto.email,
            status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateClientRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    razao_social: str
    nome_fantasia: str | None = None
    document: str
    telefone: str | None = None
    email: EmailStr | None = None


class UpdateClientRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    razao_social: str | None = None
    nome_fantasia: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None


class ClientContactResponse(BaseModel):
    id: uuid.UUID
    nome: str
    cargo: str | None
    telefone: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_dto(dto: ClientContactDTO) -> "ClientContactResponse":
        return ClientContactResponse(
            id=dto.id,
            nome=dto.nome,
            cargo=dto.cargo,
            telefone=dto.telefone,
            email=dto.email,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class CreateClientContactRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    cargo: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None


class UpdateClientContactRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    cargo: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
