from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.financial.domain.entities.bank_account import BankAccount


@dataclass(frozen=True)
class BankAccountDTO:
    id: uuid.UUID
    banco: str
    agencia: str
    numero_conta: str
    tipo: str
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(entity: BankAccount) -> "BankAccountDTO":
        return BankAccountDTO(
            id=entity.id, banco=entity.banco, agencia=entity.agencia, numero_conta=entity.numero_conta,
            tipo=entity.tipo.value, status=entity.status.value,
            created_at=entity.audit.created_at, created_by=entity.audit.created_by,
            updated_at=entity.audit.updated_at, updated_by=entity.audit.updated_by,
        )
