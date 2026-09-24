from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from modules.freight.domain.entities.manifest import Manifest


@dataclass(frozen=True)
class CargoItemDTO:
    id: uuid.UUID
    descricao: str
    peso: Decimal
    quantidade: int


@dataclass(frozen=True)
class ManifestDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    numero_documento: str | None
    itens: list[CargoItemDTO]
    trip_status_operacional: str
    """D238-style — o Romaneio conferido é a transição `CARREGANDO → EM_TRANSITO`(/`EM_ENTREGA`)
    em si; o Frontend recebe o novo status junto da resposta."""

    @staticmethod
    def from_entity(manifest: Manifest, *, trip_status_operacional: str) -> "ManifestDTO":
        return ManifestDTO(
            id=manifest.id, viagem_id=manifest.viagem_id, numero_documento=manifest.numero_documento,
            itens=[
                CargoItemDTO(id=item.id, descricao=item.descricao, peso=item.peso, quantidade=item.quantidade)
                for item in manifest.itens
            ],
            trip_status_operacional=trip_status_operacional,
        )
