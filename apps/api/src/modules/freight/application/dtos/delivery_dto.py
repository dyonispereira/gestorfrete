from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from modules.freight.domain.entities.delivery import Delivery
from modules.freight.domain.entities.delivery_window import DeliveryWindow


@dataclass(frozen=True)
class DeliveryDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    ordem: int
    destinatario: str
    endereco_entrega: dict[str, Any]
    status: str
    data_hora_conclusao: datetime | None
    motivo_recusa: str | None
    window_hora_inicio: datetime | None
    window_hora_fim: datetime | None

    @staticmethod
    def from_entity(delivery: Delivery, window: DeliveryWindow | None) -> "DeliveryDTO":
        return DeliveryDTO(
            id=delivery.id,
            viagem_id=delivery.viagem_id,
            ordem=delivery.ordem,
            destinatario=delivery.destinatario,
            endereco_entrega=delivery.endereco_entrega,
            status=delivery.status.value,
            data_hora_conclusao=delivery.data_hora_conclusao,
            motivo_recusa=delivery.motivo_recusa,
            window_hora_inicio=window.hora_inicio if window else None,
            window_hora_fim=window.hora_fim if window else None,
        )
