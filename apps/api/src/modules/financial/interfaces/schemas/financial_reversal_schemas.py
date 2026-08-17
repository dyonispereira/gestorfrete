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

    @staticmethod
    def from_dto(dto: FinancialReversalDTO) -> "FinancialReversalResponse":
        return FinancialReversalResponse(
            id=dto.id, invoice_id=dto.fatura_id, accounts_payable_id=dto.conta_pagar_id,
            accounts_receivable_id=dto.conta_receber_id, value=dto.valor, reason=dto.motivo,
            reversed_at=dto.data_hora,
        )


class CreateFinancialReversalRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: uuid.UUID | None = None
    accounts_payable_id: uuid.UUID | None = None
    accounts_receivable_id: uuid.UUID | None = None
    value: Decimal
    reason: str
