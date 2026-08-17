from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from modules.drivers.domain.entities.driver_document import DriverDocument


@dataclass(frozen=True)
class DriverDocumentDTO:
    id: uuid.UUID
    tipo_documento: str
    numero: str
    categoria_cnh: str | None
    data_validade: date | None
    status: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_entity(document: DriverDocument) -> "DriverDocumentDTO":
        return DriverDocumentDTO(
            id=document.id,
            tipo_documento=document.tipo_documento.value,
            numero=document.numero,
            categoria_cnh=document.categoria_cnh.value if document.categoria_cnh else None,
            data_validade=document.data_validade,
            status=document.status.value,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
