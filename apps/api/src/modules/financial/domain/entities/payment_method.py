from __future__ import annotations

import uuid

from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from shared_kernel.domain.base_entity import BaseEntity


class PaymentMethod(BaseEntity[uuid.UUID]):
    """`formas_pagamento` (D386) — FK `NOT NULL` de `faturas.forma_pagamento_id`. **Reconciliado
    (Lote Financeiro, Parte 2.1)**: ganhou contrato de API/RBAC próprio (`financial.payment_method.*`)
    — antes só existia via seed direto no Repository (mesmo padrão de `VehicleCategory`, D363),
    o que forçava a UI a usar um campo de ID cru. Cadastro mestre puro, sem `codigo`/`audit`
    (entidade deliberadamente mínima — só `nome`+`status`)."""

    def __init__(self, id: uuid.UUID, *, nome: str, status: PaymentMethodStatus) -> None:
        super().__init__(id)
        self.nome = nome
        self.status = status

    @classmethod
    def create(cls, *, nome: str) -> "PaymentMethod":
        return cls(id=uuid.uuid4(), nome=nome, status=PaymentMethodStatus.ATIVA)

    def update(self, *, nome: str | None, status: PaymentMethodStatus | None) -> None:
        if nome is not None:
            self.nome = nome
        if status is not None:
            self.status = status
