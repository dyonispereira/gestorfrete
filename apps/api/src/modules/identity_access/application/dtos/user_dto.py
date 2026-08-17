from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.identity_access.domain.entities.user import User


@dataclass(frozen=True)
class UserDTO:
    id: uuid.UUID
    codigo: str
    nome: str
    email: str
    status: str
    driver_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    role_ids: frozenset[uuid.UUID]
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(user: User) -> "UserDTO":
        return UserDTO(
            id=user.id,
            codigo=user.codigo,
            nome=user.nome,
            email=user.email,
            status=user.status.value,
            driver_id=user.driver_id,
            employee_id=user.employee_id,
            role_ids=user.role_ids,
            created_at=user.audit.created_at,
            created_by=user.audit.created_by,
            updated_at=user.audit.updated_at,
            updated_by=user.audit.updated_by,
        )
