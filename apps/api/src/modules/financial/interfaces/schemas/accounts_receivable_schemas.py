from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO


class AccountsReceivableResponse(BaseModel):
    id: uuid.UUID
    installment_number: int
    value: Decimal
    due_date: date
    accounting_period: date
    received_at: datetime | None
    status: str

    @staticmethod
    def from_dto(dto: AccountsReceivableDTO) -> "AccountsReceivableResponse":
        return AccountsReceivableResponse(
            id=dto.id, installment_number=dto.numero_parcela, value=dto.valor, due_date=dto.data_vencimento,
            accounting_period=dto.competencia, received_at=dto.data_recebimento, status=dto.status,
        )


class CreateAccountsReceivableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Decimal
    due_date: date
    accounting_period: date


class UpdateAccountsReceivableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Decimal | None = None
    due_date: date | None = None


class ConfirmReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    received_value: Decimal
