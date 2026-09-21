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
    `update` existe nesta entidade, só `cancel`.

    **Reconciliado (Lote Financeiro, Parte 3 — Faturamento Agrupado)**: `viagem_id` (coluna direta,
    `1 Fatura → 1 Viagem`) foi removida — substituída pelas `InvoiceTrip` filhas do agregado
    (`fatura_viagens`), permitindo `1 Fatura → N Viagens`. `entrega_id` (modo alternativo) não é
    tocado. `valor_total` deixou de ser aceito diretamente — é sempre `valor_bruto + valor_ajuste`,
    calculado em `create()`, nunca um número digitado desconectado das origens."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        numero_fatura: str,
        entrega_id: uuid.UUID | None,
        cliente_id: uuid.UUID,
        valor_bruto: Decimal,
        valor_ajuste: Decimal,
        motivo_ajuste: str | None,
        valor_total: Decimal,
        data_emissao: date,
        forma_pagamento_id: uuid.UUID,
        status: InvoiceStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.numero_fatura = numero_fatura
        self.entrega_id = entrega_id
        self.cliente_id = cliente_id
        self.valor_bruto = valor_bruto
        self.valor_ajuste = valor_ajuste
        self.motivo_ajuste = motivo_ajuste
        self.valor_total = valor_total
        self.data_emissao = data_emissao
        self.forma_pagamento_id = forma_pagamento_id
        self.status = status
        self.audit = audit

    @staticmethod
    def check_origin(*, has_trips: bool, entrega_id: uuid.UUID | None) -> None:
        """`ck_faturas_origem` reforçado no Domain — exatamente um dos dois: ao menos uma Viagem
        (via `InvoiceTrip`) OU uma Entrega, nunca os dois, nunca nenhum (Fatura nunca vazia)."""

        if has_trips == (entrega_id is not None):
            raise ValidationError(
                "FINANCIAL_INVOICE_ORIGIN_MISMATCH", "Exatamente um de trips/delivery_id é obrigatório, e trips não pode ser vazio."
            )

    @classmethod
    def create(
        cls,
        *,
        numero_fatura: str,
        has_trips: bool,
        entrega_id: uuid.UUID | None,
        cliente_id: uuid.UUID,
        valor_bruto: Decimal,
        valor_ajuste: Decimal,
        motivo_ajuste: str | None,
        data_emissao: date,
        forma_pagamento_id: uuid.UUID,
        audit: AuditMetadata,
    ) -> "Invoice":
        cls.check_origin(has_trips=has_trips, entrega_id=entrega_id)
        if valor_ajuste != 0 and not (motivo_ajuste and motivo_ajuste.strip()):
            raise ValidationError(
                "FINANCIAL_INVOICE_ADJUSTMENT_REASON_REQUIRED", "Motivo do ajuste é obrigatório quando o valor de ajuste é diferente de zero."
            )
        valor_total = valor_bruto + valor_ajuste
        if valor_total <= 0:
            raise ValidationError("FINANCIAL_INVOICE_INVALID_TOTAL", "O valor total da Fatura deve ser maior que zero.")
        return cls(
            id=uuid.uuid4(), numero_fatura=numero_fatura, entrega_id=entrega_id,
            cliente_id=cliente_id, valor_bruto=valor_bruto, valor_ajuste=valor_ajuste,
            motivo_ajuste=motivo_ajuste, valor_total=valor_total, data_emissao=data_emissao,
            forma_pagamento_id=forma_pagamento_id, status=InvoiceStatus.EMITIDA, audit=audit,
        )

    def cancel(self, *, cancelled_by: uuid.UUID, now: datetime) -> None:
        if self.status != InvoiceStatus.EMITIDA:
            raise ConflictError("FINANCIAL_INVOICE_INVALID_STATUS", "Fatura não está EMITIDA.")
        self.status = InvoiceStatus.CANCELADA
        self.audit = self.audit.touched(by=cancelled_by, at=now)
