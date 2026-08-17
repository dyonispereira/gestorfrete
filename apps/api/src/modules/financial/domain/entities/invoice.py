from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from core.exceptions.base import ConflictError, ValidationError
from modules.financial.domain.value_objects.invoice_status import InvoiceStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Invoice(BaseAggregateRoot[uuid.UUID]):
    """`faturas` — Fatura (D260, CRUD mínimo pré-requisito de Contas a Receber). D273: `CANCELADA`
    existe de fato aqui (único comando real, `commands/cancel`). D391 — ganha o bloco padrão de
    auditoria, ausente na DDL congelada. `valor_total` imutável após emitida (D100) — nenhum método
    `update` existe nesta entidade, só `cancel`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        numero_fatura: str,
        viagem_id: uuid.UUID | None,
        entrega_id: uuid.UUID | None,
        cliente_id: uuid.UUID,
        valor_total: Decimal,
        data_emissao: date,
        forma_pagamento_id: uuid.UUID,
        status: InvoiceStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.numero_fatura = numero_fatura
        self.viagem_id = viagem_id
        self.entrega_id = entrega_id
        self.cliente_id = cliente_id
        self.valor_total = valor_total
        self.data_emissao = data_emissao
        self.forma_pagamento_id = forma_pagamento_id
        self.status = status
        self.audit = audit

    @staticmethod
    def check_origin(*, viagem_id: uuid.UUID | None, entrega_id: uuid.UUID | None) -> None:
        """`ck_faturas_origem` reforçado no Domain — exatamente um dos dois."""

        if (viagem_id is not None) == (entrega_id is not None):
            raise ValidationError(
                "FINANCIAL_INVOICE_ORIGIN_MISMATCH", "Exatamente um de trip_id/delivery_id é obrigatório."
            )

    @classmethod
    def create(
        cls,
        *,
        numero_fatura: str,
        viagem_id: uuid.UUID | None,
        entrega_id: uuid.UUID | None,
        cliente_id: uuid.UUID,
        valor_total: Decimal,
        data_emissao: date,
        forma_pagamento_id: uuid.UUID,
        audit: AuditMetadata,
    ) -> "Invoice":
        cls.check_origin(viagem_id=viagem_id, entrega_id=entrega_id)
        return cls(
            id=uuid.uuid4(), numero_fatura=numero_fatura, viagem_id=viagem_id, entrega_id=entrega_id,
            cliente_id=cliente_id, valor_total=valor_total, data_emissao=data_emissao,
            forma_pagamento_id=forma_pagamento_id, status=InvoiceStatus.EMITIDA, audit=audit,
        )

    def cancel(self, *, cancelled_by: uuid.UUID, now: datetime) -> None:
        if self.status != InvoiceStatus.EMITIDA:
            raise ConflictError("FINANCIAL_INVOICE_INVALID_STATUS", "Fatura não está EMITIDA.")
        self.status = InvoiceStatus.CANCELADA
        self.audit = self.audit.touched(by=cancelled_by, at=now)
