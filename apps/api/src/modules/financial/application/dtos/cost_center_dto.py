from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.financial.domain.entities.cost_center import CostCenter


@dataclass(frozen=True)
class CostCenterDTO:
    id: uuid.UUID
    codigo: str
    codigo_contabil: str
    nome: str
    filial_id: uuid.UUID | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(cost_center: CostCenter) -> "CostCenterDTO":
        return CostCenterDTO(
            id=cost_center.id,
            codigo=cost_center.codigo,
            codigo_contabil=cost_center.codigo_contabil,
            nome=cost_center.nome,
            filial_id=cost_center.filial_id,
            status=cost_center.status.value,
            created_at=cost_center.audit.created_at,
            created_by=cost_center.audit.created_by,
            updated_at=cost_center.audit.updated_at,
            updated_by=cost_center.audit.updated_by,
        )
