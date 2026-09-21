from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.invoice_dto import InvoiceDTO, InvoiceTripDTO
from modules.financial.application.queries.list_eligible_trips_for_invoice import EligibleTripDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class InvoiceTripResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    value: Decimal

    @staticmethod
    def from_dto(dto: InvoiceTripDTO) -> "InvoiceTripResponse":
        return InvoiceTripResponse(id=dto.id, trip_id=dto.viagem_id, value=dto.valor)


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    delivery_id: uuid.UUID | None
    client_id: uuid.UUID
    gross_value: Decimal
    adjustment_value: Decimal
    adjustment_reason: str | None
    total_value: Decimal
    issue_date: date
    payment_method_id: uuid.UUID
    status: str
    # Lote Financeiro, Parte 3 — Faturamento Agrupado. Vazio no modo "por entrega".
    trips: list[InvoiceTripResponse]
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: InvoiceDTO) -> "InvoiceResponse":
        return InvoiceResponse(
            id=dto.id, invoice_number=dto.numero_fatura, delivery_id=dto.entrega_id,
            client_id=dto.cliente_id, gross_value=dto.valor_bruto, adjustment_value=dto.valor_ajuste,
            adjustment_reason=dto.motivo_ajuste, total_value=dto.valor_total, issue_date=dto.data_emissao,
            payment_method_id=dto.forma_pagamento_id, status=dto.status,
            trips=[InvoiceTripResponse.from_dto(t) for t in dto.trips],
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by,
                updated_at=dto.updated_at, updated_by=dto.updated_by,
            ),
        )


class EligibleTripResponse(BaseModel):
    trip_id: uuid.UUID
    codigo: str
    scheduled_date: date | None
    suggested_value: Decimal | None

    @staticmethod
    def from_dto(dto: EligibleTripDTO) -> "EligibleTripResponse":
        return EligibleTripResponse(
            trip_id=dto.trip_id, codigo=dto.codigo, scheduled_date=dto.data_programada,
            suggested_value=dto.suggested_value,
        )


class InvoiceInstallmentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Decimal
    due_date: date
    accounting_period: date


class InvoiceTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trip_id: uuid.UUID
    value: Decimal


class CreateInvoiceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trips: list[InvoiceTripRequest] = []
    delivery_id: uuid.UUID | None = None
    client_id: uuid.UUID
    adjustment_value: Decimal = Decimal("0")
    adjustment_reason: str | None = None
    payment_method_id: uuid.UUID
    installments: list[InvoiceInstallmentRequest]
