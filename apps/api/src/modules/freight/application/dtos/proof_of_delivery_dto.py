from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.freight.domain.entities.proof_of_delivery import ProofOfDelivery


@dataclass(frozen=True)
class ProofOfDeliveryDTO:
    id: uuid.UUID
    entrega_id: uuid.UUID
    status: str
    data_hora_registro: datetime | None
    assinatura_arquivo_id: uuid.UUID | None

    @staticmethod
    def from_entity(pod: ProofOfDelivery) -> "ProofOfDeliveryDTO":
        return ProofOfDeliveryDTO(
            id=pod.id,
            entrega_id=pod.entrega_id,
            status=pod.status.value,
            data_hora_registro=pod.data_hora_registro,
            assinatura_arquivo_id=pod.assinatura_arquivo_id,
        )
