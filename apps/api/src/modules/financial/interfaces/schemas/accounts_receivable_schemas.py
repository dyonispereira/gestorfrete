from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.accounts_receivable_dto import AccountsReceivableDTO


class AccountsReceivableResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    installment_number: int
    value: Decimal
    # `received_value`/`open_balance` — Lote Financeiro, Parte 2.1 (baixa parcial real).
    received_value: Decimal
    open_balance: Decimal
    due_date: date
    accounting_period: date
    received_at: datetime | None
    status: str
    # Só preenchido por `GET /contas-receber` (consulta agregada, Lote Financeiro Parte 2.1) — `null`
    # nas rotas aninhadas sob `/faturas/{invoice_id}/contas-receber`, onde o cliente já é conhecido
    # pela própria Fatura.
    client_id: uuid.UUID | None = None

    @staticmethod
    def from_dto(dto: AccountsReceivableDTO) -> "AccountsReceivableResponse":
        return AccountsReceivableResponse(
            id=dto.id, invoice_id=dto.fatura_id, installment_number=dto.numero_parcela, value=dto.valor,
            received_value=dto.valor_recebido, open_balance=dto.saldo_aberto, due_date=dto.data_vencimento,
            accounting_period=dto.competencia, received_at=dto.data_recebimento,
            status=dto.status, client_id=dto.cliente_id,
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
