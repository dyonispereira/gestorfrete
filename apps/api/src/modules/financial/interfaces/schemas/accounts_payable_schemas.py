from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.accounts_payable_dto import AccountsPayableDTO
from modules.financial.application.dtos.expense_allocation_dto import ExpenseAllocationDTO
from modules.financial.application.dtos.expense_approval_dto import ExpenseApprovalDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class AccountsPayableResponse(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    cost_center_id: uuid.UUID
    origin: str
    trip_id: uuid.UUID | None
    maintenance_order_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    driver_id: uuid.UUID | None
    value: Decimal
    due_date: date
    accounting_period: date
    chart_of_accounts_id: uuid.UUID
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: AccountsPayableDTO) -> "AccountsPayableResponse":
        return AccountsPayableResponse(
            id=dto.id, supplier_id=dto.fornecedor_id, cost_center_id=dto.centro_custo_id, origin=dto.origem,
            trip_id=dto.viagem_id, maintenance_order_id=dto.ordem_servico_id, vehicle_id=dto.veiculo_tracionador_id,
            driver_id=dto.motorista_id, value=dto.valor, due_date=dto.data_vencimento,
            accounting_period=dto.competencia, chart_of_accounts_id=dto.plano_contas_id, status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by,
                updated_at=dto.updated_at, updated_by=dto.updated_by,
            ),
        )


class ExpenseApprovalResponse(BaseModel):
    id: uuid.UUID
    decision: str
    justification: str | None
    actor_id: uuid.UUID
    decided_at: datetime

    @staticmethod
    def from_dto(dto: ExpenseApprovalDTO) -> "ExpenseApprovalResponse":
        return ExpenseApprovalResponse(
            id=dto.id, decision=dto.decisao, justification=dto.justificativa,
            actor_id=dto.ator_id, decided_at=dto.data_hora,
        )


class ExpenseAllocationResponse(BaseModel):
    id: uuid.UUID
    cost_center_id: uuid.UUID | None
    trip_id: uuid.UUID | None
    criterion: str
    allocated_value: Decimal

    @staticmethod
    def from_dto(dto: ExpenseAllocationDTO) -> "ExpenseAllocationResponse":
        return ExpenseAllocationResponse(
            id=dto.id, cost_center_id=dto.centro_custo_id, trip_id=dto.viagem_id,
            criterion=dto.criterio, allocated_value=dto.valor_rateado,
        )


class CreateAccountsPayableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    supplier_id: uuid.UUID
    cost_center_id: uuid.UUID
    origin: str
    trip_id: uuid.UUID | None = None
    maintenance_order_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    value: Decimal
    due_date: date
    accounting_period: date
    chart_of_accounts_id: uuid.UUID


class UpdateAccountsPayableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    supplier_id: uuid.UUID | None = None
    cost_center_id: uuid.UUID | None = None
    value: Decimal | None = None
    due_date: date | None = None
    chart_of_accounts_id: uuid.UUID | None = None


class ExpenseDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str | None = None


class PayAccountsPayableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bank_account_id: uuid.UUID
