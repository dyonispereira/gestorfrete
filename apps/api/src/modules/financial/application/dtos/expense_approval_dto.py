from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.financial.domain.entities.expense_approval import ExpenseApproval


@dataclass(frozen=True)
class ExpenseApprovalDTO:
    id: uuid.UUID
    decisao: str
    justificativa: str | None
    ator_id: uuid.UUID
    data_hora: datetime

    @staticmethod
    def from_entity(entity: ExpenseApproval) -> "ExpenseApprovalDTO":
        return ExpenseApprovalDTO(
            id=entity.id, decisao=entity.decisao.value, justificativa=entity.justificativa, ator_id=entity.ator_id,
            data_hora=entity.data_hora,
        )
