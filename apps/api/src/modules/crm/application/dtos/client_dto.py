from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.crm.domain.entities.client import Client


@dataclass(frozen=True)
class ClientDTO:
    id: uuid.UUID
    codigo: str
    razao_social: str
    nome_fantasia: str | None
    document: str
    telefone: str | None
    email: str | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(client: Client) -> "ClientDTO":
        return ClientDTO(
            id=client.id,
            codigo=client.codigo,
            razao_social=client.razao_social,
            nome_fantasia=client.nome_fantasia,
            document=client.document,
            telefone=client.telefone,
            email=client.email,
            status=client.status.value,
            created_at=client.audit.created_at,
            created_by=client.audit.created_by,
            updated_at=client.audit.updated_at,
            updated_by=client.audit.updated_by,
        )
