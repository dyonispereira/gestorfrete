from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ValidationError
from shared_kernel.domain.base_entity import BaseEntity


class InvoiceTrip(BaseEntity[uuid.UUID]):
    """`fatura_viagens` (Lote Financeiro, Parte 3 — Faturamento Agrupado) — Fatura Viagem, item do
    agregado Fatura. Substitui `faturas.viagem_id` (coluna direta, `1 Fatura → 1 Viagem`), que é
    removida. Nunca referencia Entrega/CT-e diretamente (D008) — essa navegação acontece a partir
    da própria Viagem, que já expõe suas Entregas e seu CT-e. Imutável após criada, mesmo princípio
    de `valor_total` da Fatura (D100) — correção via Estorno Financeiro, nunca edição."""

    def __init__(self, id: uuid.UUID, *, fatura_id: uuid.UUID, viagem_id: uuid.UUID, valor: Decimal, criado_em: datetime) -> None:
        super().__init__(id)
        self.fatura_id = fatura_id
        self.viagem_id = viagem_id
        self.valor = valor
        self.criado_em = criado_em

    @classmethod
    def create(cls, *, fatura_id: uuid.UUID, viagem_id: uuid.UUID, valor: Decimal, now: datetime) -> "InvoiceTrip":
        if valor <= 0:
            raise ValidationError("FINANCIAL_INVOICE_TRIP_INVALID_VALUE", "O valor de cada Viagem faturada deve ser maior que zero.")
        return cls(id=uuid.uuid4(), fatura_id=fatura_id, viagem_id=viagem_id, valor=valor, criado_em=now)
