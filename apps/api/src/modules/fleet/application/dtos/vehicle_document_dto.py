from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from modules.fleet.domain.entities.vehicle_document import VehicleDocument


@dataclass(frozen=True)
class VehicleDocumentDTO:
    id: uuid.UUID
    tipo: str
    numero: str
    data_validade: date
    status: str
    arquivo_id: uuid.UUID | None

    @staticmethod
    def from_entity(document: VehicleDocument) -> "VehicleDocumentDTO":
        return VehicleDocumentDTO(
            id=document.id,
            tipo=document.tipo,
            numero=document.numero,
            data_validade=document.data_validade,
            status=document.status.value,
            arquivo_id=document.arquivo_id,
        )
