from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.financial.domain.entities.payment_method import PaymentMethod


@dataclass(frozen=True)
class PaymentMethodDTO:
    id: uuid.UUID
    nome: str
    status: str

    @staticmethod
    def from_entity(entity: PaymentMethod) -> "PaymentMethodDTO":
        return PaymentMethodDTO(id=entity.id, nome=entity.nome, status=entity.status.value)
