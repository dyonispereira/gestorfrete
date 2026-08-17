from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.bank_account_dto import BankAccountDTO
from modules.financial.application.queries.get_bank_account_balance import BankAccountBalanceResult
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class BankAccountResponse(BaseModel):
    id: uuid.UUID
    bank: str
    branch: str
    account_number: str
    type: str
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: BankAccountDTO) -> "BankAccountResponse":
        return BankAccountResponse(
            id=dto.id, bank=dto.banco, branch=dto.agencia, account_number=dto.numero_conta,
            type=dto.tipo, status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by,
                updated_at=dto.updated_at, updated_by=dto.updated_by,
            ),
        )


class BankAccountBalanceResponse(BaseModel):
    bank_account_id: uuid.UUID
    balance: Decimal
    calculated_at: datetime

    @staticmethod
    def from_result(result: BankAccountBalanceResult) -> "BankAccountBalanceResponse":
        return BankAccountBalanceResponse(
            bank_account_id=result.bank_account_id, balance=result.balance, calculated_at=result.calculated_at
        )


class CreateBankAccountRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bank: str
    branch: str
    account_number: str
    type: str


class UpdateBankAccountRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bank: str | None = None
    branch: str | None = None
    status: str | None = None
