from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import DomainError
from shared_kernel.domain.base_entity import BaseEntity


class DeliveryWindow(BaseEntity[uuid.UUID]):
    """`janelas_entrega` — 1:1 com Entrega (`uq_janelas_entrega_entrega_id`). Sem endpoint próprio,
    só existe como parte do payload de criação de uma `Delivery` (`DELIVERY_IMPLEMENTATION.md`)."""

    def __init__(self, id: uuid.UUID, *, entrega_id: uuid.UUID, hora_inicio: datetime, hora_fim: datetime) -> None:
        super().__init__(id)
        self.entrega_id = entrega_id
        self.hora_inicio = hora_inicio
        self.hora_fim = hora_fim

    @classmethod
    def create(cls, *, entrega_id: uuid.UUID, hora_inicio: datetime, hora_fim: datetime) -> "DeliveryWindow":
        if hora_fim <= hora_inicio:
            raise DomainError(
                "FREIGHT_DELIVERY_WINDOW_INVALID", "O fim da janela de entrega deve ser posterior ao início."
            )
        return cls(id=uuid.uuid4(), entrega_id=entrega_id, hora_inicio=hora_inicio, hora_fim=hora_fim)
