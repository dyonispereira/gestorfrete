from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from modules.identity_access.domain.entities.employee import Employee


@dataclass(frozen=True)
class EmployeeDTO:
    id: uuid.UUID
    codigo: str
    nome: str
    cargo: str
    data_admissao: date | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(employee: Employee) -> "EmployeeDTO":
        return EmployeeDTO(
            id=employee.id,
            codigo=employee.codigo,
            nome=employee.nome,
            cargo=employee.cargo,
            data_admissao=employee.data_admissao,
            status=employee.status.value,
            created_at=employee.audit.created_at,
            created_by=employee.audit.created_by,
            updated_at=employee.audit.updated_at,
            updated_by=employee.audit.updated_by,
        )
