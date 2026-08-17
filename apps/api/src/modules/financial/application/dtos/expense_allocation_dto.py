from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.financial.domain.entities.expense_allocation import ExpenseAllocation


@dataclass(frozen=True)
class ExpenseAllocationDTO:
    id: uuid.UUID
    centro_custo_id: uuid.UUID | None
    viagem_id: uuid.UUID | None
    criterio: str
    valor_rateado: Decimal

    @staticmethod
    def from_entity(entity: ExpenseAllocation) -> "ExpenseAllocationDTO":
        return ExpenseAllocationDTO(
            id=entity.id, centro_custo_id=entity.centro_custo_id, viagem_id=entity.viagem_id,
            criterio=entity.criterio.value, valor_rateado=entity.valor_rateado,
        )
