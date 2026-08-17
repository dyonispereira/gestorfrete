from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ValidationError
from shared_kernel.domain.base_entity import BaseEntity


class FinancialReversal(BaseEntity[uuid.UUID]):
    """`estornos_financeiros` — Estorno Financeiro (D266). Mecanismo único de correção pós-fato
    para Fatura/Conta a Pagar/Conta a Receber. **Nunca** altera o alvo — só existe como registro
    paralelo, imutável (auditoria #3 do usuário: o lançamento original continua historicamente
    liquidado, o Estorno é sua própria trilha)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        fatura_id: uuid.UUID | None,
        conta_pagar_id: uuid.UUID | None,
        conta_receber_id: uuid.UUID | None,
        valor: Decimal,
        motivo: str,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.fatura_id = fatura_id
        self.conta_pagar_id = conta_pagar_id
        self.conta_receber_id = conta_receber_id
        self.valor = valor
        self.motivo = motivo
        self.data_hora = data_hora

    @staticmethod
    def check_target(
        *, fatura_id: uuid.UUID | None, conta_pagar_id: uuid.UUID | None, conta_receber_id: uuid.UUID | None
    ) -> None:
        """`ck_estornos_financeiros_alvo_exclusivo` reforçado no Domain — exatamente um dos três."""

        target_count = sum(1 for target in (fatura_id, conta_pagar_id, conta_receber_id) if target is not None)
        if target_count != 1:
            raise ValidationError(
                "FINANCIAL_REVERSAL_TARGET_MISMATCH", "Exatamente um de invoice_id/accounts_payable_id/accounts_receivable_id é obrigatório."
            )

    @classmethod
    def create(
        cls,
        *,
        fatura_id: uuid.UUID | None,
        conta_pagar_id: uuid.UUID | None,
        conta_receber_id: uuid.UUID | None,
        valor: Decimal,
        motivo: str,
        now: datetime,
    ) -> "FinancialReversal":
        cls.check_target(fatura_id=fatura_id, conta_pagar_id=conta_pagar_id, conta_receber_id=conta_receber_id)
        return cls(
            id=uuid.uuid4(), fatura_id=fatura_id, conta_pagar_id=conta_pagar_id, conta_receber_id=conta_receber_id,
            valor=valor, motivo=motivo, data_hora=now,
        )
