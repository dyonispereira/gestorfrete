from __future__ import annotations

import uuid

from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from shared_kernel.domain.base_entity import BaseEntity


class PaymentMethod(BaseEntity[uuid.UUID]):
    """`formas_pagamento` (D386) — FK `NOT NULL` de `faturas.forma_pagamento_id`, sem endpoint HTTP
    (sem contrato de API/RBAC próprio). Seed direto via Repository nos testes, mesmo padrão de
    `VehicleCategory` (D363)."""

    def __init__(self, id: uuid.UUID, *, nome: str, status: PaymentMethodStatus) -> None:
        super().__init__(id)
        self.nome = nome
        self.status = status

    @classmethod
    def create(cls, *, nome: str) -> "PaymentMethod":
        return cls(id=uuid.uuid4(), nome=nome, status=PaymentMethodStatus.ATIVA)
