from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from modules.financial.domain.entities.invoice import Invoice


@dataclass(frozen=True)
class InvoiceDTO:
    id: uuid.UUID
    numero_fatura: str
    viagem_id: uuid.UUID | None
    entrega_id: uuid.UUID | None
    cliente_id: uuid.UUID
    valor_total: Decimal
    data_emissao: date
    forma_pagamento_id: uuid.UUID
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(entity: Invoice) -> "InvoiceDTO":
        return InvoiceDTO(
            id=entity.id, numero_fatura=entity.numero_fatura, viagem_id=entity.viagem_id,
            entrega_id=entity.entrega_id, cliente_id=entity.cliente_id, valor_total=entity.valor_total,
            data_emissao=entity.data_emissao, forma_pagamento_id=entity.forma_pagamento_id,
            status=entity.status.value, created_at=entity.audit.created_at, created_by=entity.audit.created_by,
            updated_at=entity.audit.updated_at, updated_by=entity.audit.updated_by,
        )
