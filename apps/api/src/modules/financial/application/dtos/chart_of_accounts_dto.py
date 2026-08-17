from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.financial.domain.entities.chart_of_accounts import ChartOfAccounts


@dataclass(frozen=True)
class ChartOfAccountsDTO:
    id: uuid.UUID
    codigo_contabil: str
    nome: str
    tipo: str
    categoria_pai_id: uuid.UUID | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(entity: ChartOfAccounts) -> "ChartOfAccountsDTO":
        return ChartOfAccountsDTO(
            id=entity.id, codigo_contabil=entity.codigo_contabil, nome=entity.nome, tipo=entity.tipo.value,
            categoria_pai_id=entity.categoria_pai_id, status=entity.status.value,
            created_at=entity.audit.created_at, created_by=entity.audit.created_by,
            updated_at=entity.audit.updated_at, updated_by=entity.audit.updated_by,
        )
