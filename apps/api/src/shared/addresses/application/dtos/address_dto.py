from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from shared.addresses.domain.entities.address import Address


@dataclass(frozen=True)
class AddressDTO:
    id: uuid.UUID
    tipo: str
    logradouro: str
    numero: str | None
    complemento: str | None
    bairro: str
    cidade: str
    uf: str
    cep: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(address: Address) -> "AddressDTO":
        return AddressDTO(
            id=address.id,
            tipo=address.tipo.value,
            logradouro=address.logradouro,
            numero=address.numero,
            complemento=address.complemento,
            bairro=address.bairro,
            cidade=address.cidade,
            uf=address.uf,
            cep=address.cep,
            created_at=address.audit.created_at,
            created_by=address.audit.created_by,
            updated_at=address.audit.updated_at,
            updated_by=address.audit.updated_by,
        )
