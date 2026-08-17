from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.tracking.domain.entities.tracking_provider import TrackingProvider


@dataclass(frozen=True)
class TrackingProviderDTO:
    id: uuid.UUID
    nome: str
    status: str

    @staticmethod
    def from_entity(entity: TrackingProvider) -> "TrackingProviderDTO":
        return TrackingProviderDTO(id=entity.id, nome=entity.nome, status=entity.status.value)
