from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.addresses.application.dtos.address_dto import AddressDTO


class AddressAuditResponse(BaseModel):
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None


class AddressResponse(BaseModel):
    """Schema `Address` (`docs/api/011-addresses.md`) — reusado por todo módulo dono
    (`crm`/`maintenance`, futuramente `tenancy`): o recurso é idêntico por contrato, nenhuma cópia
    por consumidor (`ADDRESS_IMPLEMENTATION.md`)."""

    id: uuid.UUID
    type: str
    logradouro: str
    numero: str | None
    complemento: str | None
    bairro: str
    cidade: str
    uf: str
    cep: str
    audit: AddressAuditResponse

    @staticmethod
    def from_dto(dto: AddressDTO) -> "AddressResponse":
        return AddressResponse(
            id=dto.id,
            type=dto.tipo,
            logradouro=dto.logradouro,
            numero=dto.numero,
            complemento=dto.complemento,
            bairro=dto.bairro,
            cidade=dto.cidade,
            uf=dto.uf,
            cep=dto.cep,
            audit=AddressAuditResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateAddressRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    logradouro: str
    numero: str | None = None
    complemento: str | None = None
    bairro: str
    cidade: str
    uf: str
    cep: str


class UpdateAddressRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    cep: str | None = None
