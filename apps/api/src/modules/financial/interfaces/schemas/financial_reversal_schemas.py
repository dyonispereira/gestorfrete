from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.financial_reversal_dto import FinancialReversalDTO


class FinancialReversalResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID | None
    accounts_payable_id: uuid.UUID | None
    accounts_receivable_id: uuid.UUID | None
    value: Decimal
    reason: str
    reversed_at: datetime
    # Lote Financeiro, Parte 2.1 — resolvido via `logs_auditoria` (D266: `FinancialReversal` nunca
    # teve `ator_id` próprio; a trilha transversal já capturava isso). `null` se o registro de
    # auditoria da criação não existir (nunca deveria acontecer, mas não é uma garantia de FK).
    created_by: uuid.UUID | None

    @staticmethod
    def from_dto(dto: FinancialReversalDTO) -> "FinancialReversalResponse":
        return FinancialReversalResponse(
            id=dto.id, invoice_id=dto.fatura_id, accounts_payable_id=dto.conta_pagar_id,
            accounts_receivable_id=dto.conta_receber_id, value=dto.valor, reason=dto.motivo,
            reversed_at=dto.data_hora, created_by=dto.criado_por,
        )


class CreateFinancialReversalRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: uuid.UUID | None = None
    accounts_payable_id: uuid.UUID | None = None
    accounts_receivable_id: uuid.UUID | None = None
    value: Decimal
    reason: str
