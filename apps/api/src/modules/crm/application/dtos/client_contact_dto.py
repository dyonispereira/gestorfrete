from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.crm.domain.entities.client_contact import ClientContact


@dataclass(frozen=True)
class ClientContactDTO:
    id: uuid.UUID
    nome: str
    cargo: str | None
    telefone: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_entity(contact: ClientContact) -> "ClientContactDTO":
        return ClientContactDTO(
            id=contact.id,
            nome=contact.nome,
            cargo=contact.cargo,
            telefone=contact.telefone,
            email=contact.email,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
