from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr

from modules.drivers.application.dtos.driver_document_dto import DriverDocumentDTO
from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class DriverResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nome: str
    cpf: str
    telefone: str | None
    email: str | None
    employment_type: str
    fitness_status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: DriverDTO) -> "DriverResponse":
        return DriverResponse(
            id=dto.id,
            codigo=dto.codigo,
            nome=dto.nome,
            cpf=dto.cpf,
            telefone=dto.telefone,
            email=dto.email,
            employment_type=dto.employment_type,
            fitness_status=dto.fitness_status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateDriverRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    cpf: str
    telefone: str | None = None
    email: EmailStr | None = None
    employment_type: str


class UpdateDriverRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None


class DriverDocumentResponse(BaseModel):
    id: uuid.UUID
    type: str
    number: str
    cnh_category: str | None
    expires_at: date | None
    status: str

    @staticmethod
    def from_dto(dto: DriverDocumentDTO) -> "DriverDocumentResponse":
        return DriverDocumentResponse(
            id=dto.id,
            type=dto.tipo_documento,
            number=dto.numero,
            cnh_category=dto.categoria_cnh,
            expires_at=dto.data_validade,
            status=dto.status,
        )


class CreateDriverDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    number: str
    cnh_category: str | None = None
    expires_at: date | None = None


class UpdateDriverDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: str | None = None
    cnh_category: str | None = None
    expires_at: date | None = None
