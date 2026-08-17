from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from core.exceptions.base import DomainError
from modules.freight.domain.value_objects.delivery_status import TERMINAL_DELIVERY_STATUSES, DeliveryStatus
from shared_kernel.domain.base_entity import BaseEntity


class Delivery(BaseEntity[uuid.UUID]):
    """`entregas` — sub-recurso de `Trip` (D232), multi-drop real via `UNIQUE (viagem_id, ordem)`,
    nunca colunas `entrega1`/`entrega2`. Diferente de `Trip.status_operacional`, `status` **é**
    editável por `PATCH` direto (`015-trip-deliveries.md`, D233 se aplica só à Viagem)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        ordem: int,
        destinatario: str,
        endereco_entrega: dict[str, Any],
        status: DeliveryStatus,
        data_hora_conclusao: datetime | None,
        motivo_recusa: str | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.ordem = ordem
        self.destinatario = destinatario
        self.endereco_entrega = endereco_entrega
        self.status = status
        self.data_hora_conclusao = data_hora_conclusao
        self.motivo_recusa = motivo_recusa

    @classmethod
    def create(
        cls, *, viagem_id: uuid.UUID, ordem: int, destinatario: str, endereco_entrega: dict[str, Any]
    ) -> "Delivery":
        return cls(
            id=uuid.uuid4(),
            viagem_id=viagem_id,
            ordem=ordem,
            destinatario=destinatario,
            endereco_entrega=endereco_entrega,
            status=DeliveryStatus.PENDENTE,
            data_hora_conclusao=None,
            motivo_recusa=None,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_DELIVERY_STATUSES

    def update(
        self,
        *,
        destinatario: str | None,
        endereco_entrega: dict[str, Any] | None,
        status: DeliveryStatus | None,
        rejection_reason: str | None,
        now: datetime,
    ) -> None:
        if destinatario is not None:
            self.destinatario = destinatario
        if endereco_entrega is not None:
            self.endereco_entrega = endereco_entrega
        if status is not None:
            if status == DeliveryStatus.RECUSADA and not rejection_reason:
                raise DomainError(
                    "FREIGHT_DELIVERY_REJECTION_REASON_REQUIRED",
                    "motivo_recusa é obrigatório quando status = RECUSADA.",
                )
            self.status = status
            if status == DeliveryStatus.RECUSADA:
                self.motivo_recusa = rejection_reason
            if status in TERMINAL_DELIVERY_STATUSES:
                self.data_hora_conclusao = now
