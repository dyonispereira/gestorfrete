from __future__ import annotations

import uuid
from datetime import datetime

from modules.financial.domain.value_objects.expense_approval_decision import ExpenseApprovalDecision
from shared_kernel.domain.base_entity import BaseEntity


class ExpenseApproval(BaseEntity[uuid.UUID]):
    """`aprovacoes_despesa` — histórico de decisões sobre uma Conta a Pagar (normalmente 0 ou 1
    registro, múltiplos níveis é requisito futuro). Imutável após criada."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        conta_pagar_id: uuid.UUID,
        decisao: ExpenseApprovalDecision,
        justificativa: str | None,
        ator_id: uuid.UUID,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.conta_pagar_id = conta_pagar_id
        self.decisao = decisao
        self.justificativa = justificativa
        self.ator_id = ator_id
        self.data_hora = data_hora

    @classmethod
    def create(
        cls,
        *,
        conta_pagar_id: uuid.UUID,
        decisao: ExpenseApprovalDecision,
        justificativa: str | None,
        ator_id: uuid.UUID,
        now: datetime,
    ) -> "ExpenseApproval":
        return cls(
            id=uuid.uuid4(), conta_pagar_id=conta_pagar_id, decisao=decisao, justificativa=justificativa,
            ator_id=ator_id, data_hora=now,
        )
