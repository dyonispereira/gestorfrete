from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.identity_access.domain.entities.role import Role


@dataclass(frozen=True)
class RoleDTO:
    id: uuid.UUID
    codigo: str
    nome: str
    descricao: str | None
    permission_codes: list[str]
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(role: Role, permission_codes: list[str]) -> "RoleDTO":
        return RoleDTO(
            id=role.id,
            codigo=role.codigo,
            nome=role.nome,
            descricao=role.descricao,
            permission_codes=sorted(permission_codes),
            created_at=role.audit.created_at,
            created_by=role.audit.created_by,
            updated_at=role.audit.updated_at,
            updated_by=role.audit.updated_by,
        )
