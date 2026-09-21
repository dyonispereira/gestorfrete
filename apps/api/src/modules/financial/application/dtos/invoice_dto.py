from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from modules.financial.domain.entities.invoice import Invoice
from modules.financial.domain.entities.invoice_trip import InvoiceTrip


@dataclass(frozen=True)
class InvoiceTripDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    valor: Decimal

    @staticmethod
    def from_entity(entity: InvoiceTrip) -> "InvoiceTripDTO":
        return InvoiceTripDTO(id=entity.id, viagem_id=entity.viagem_id, valor=entity.valor)


@dataclass(frozen=True)
class InvoiceDTO:
    id: uuid.UUID
    numero_fatura: str
    entrega_id: uuid.UUID | None
    cliente_id: uuid.UUID
    valor_bruto: Decimal
    valor_ajuste: Decimal
    motivo_ajuste: str | None
    valor_total: Decimal
    data_emissao: date
    forma_pagamento_id: uuid.UUID
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None
    # Lote Financeiro, Parte 3 — Faturamento Agrupado. Vazio no modo "por entrega".
    trips: list[InvoiceTripDTO] = field(default_factory=list)

    @staticmethod
    def from_entity(entity: Invoice, *, trips: list[InvoiceTripDTO] = ()) -> "InvoiceDTO":  # type: ignore[assignment]
        return InvoiceDTO(
            id=entity.id, numero_fatura=entity.numero_fatura,
            entrega_id=entity.entrega_id, cliente_id=entity.cliente_id, valor_bruto=entity.valor_bruto,
            valor_ajuste=entity.valor_ajuste, motivo_ajuste=entity.motivo_ajuste, valor_total=entity.valor_total,
            data_emissao=entity.data_emissao, forma_pagamento_id=entity.forma_pagamento_id,
            status=entity.status.value, created_at=entity.audit.created_at, created_by=entity.audit.created_by,
            updated_at=entity.audit.updated_at, updated_by=entity.audit.updated_by, trips=list(trips),
        )
