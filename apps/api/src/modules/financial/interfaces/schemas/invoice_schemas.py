from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.invoice_dto import InvoiceDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    trip_id: uuid.UUID | None
    delivery_id: uuid.UUID | None
    client_id: uuid.UUID
    total_value: Decimal
    issue_date: date
    payment_method_id: uuid.UUID
    status: str
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: InvoiceDTO) -> "InvoiceResponse":
        return InvoiceResponse(
            id=dto.id, invoice_number=dto.numero_fatura, trip_id=dto.viagem_id, delivery_id=dto.entrega_id,
            client_id=dto.cliente_id, total_value=dto.valor_total, issue_date=dto.data_emissao,
            payment_method_id=dto.forma_pagamento_id, status=dto.status,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by,
                updated_at=dto.updated_at, updated_by=dto.updated_by,
            ),
        )


class InvoiceInstallmentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Decimal
    due_date: date


class CreateInvoiceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trip_id: uuid.UUID | None = None
    delivery_id: uuid.UUID | None = None
    client_id: uuid.UUID
    total_value: Decimal
    payment_method_id: uuid.UUID
    installments: list[InvoiceInstallmentRequest]
