from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.drivers.domain.entities.driver import Driver


@dataclass(frozen=True)
class DriverDTO:
    id: uuid.UUID
    codigo: str
    nome: str
    cpf: str
    telefone: str | None
    email: str | None
    employment_type: str
    fitness_status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(driver: Driver) -> "DriverDTO":
        return DriverDTO(
            id=driver.id,
            codigo=driver.codigo,
            nome=driver.nome,
            cpf=driver.cpf,
            telefone=driver.telefone,
            email=driver.email,
            employment_type=driver.employment_type.value,
            fitness_status=driver.fitness_status.value,
            created_at=driver.audit.created_at,
            created_by=driver.audit.created_by,
            updated_at=driver.audit.updated_at,
            updated_by=driver.audit.updated_by,
        )
