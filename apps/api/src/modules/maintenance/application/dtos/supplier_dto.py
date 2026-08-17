from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.maintenance.domain.entities.supplier import Supplier


@dataclass(frozen=True)
class SupplierDTO:
    id: uuid.UUID
    codigo: str
    razao_social: str
    cnpj: str
    telefone: str | None
    category: str | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(supplier: Supplier) -> "SupplierDTO":
        return SupplierDTO(
            id=supplier.id,
            codigo=supplier.codigo,
            razao_social=supplier.razao_social,
            cnpj=supplier.cnpj,
            telefone=supplier.telefone,
            category=supplier.category.value if supplier.category else None,
            status=supplier.status.value,
            created_at=supplier.audit.created_at,
            created_by=supplier.audit.created_by,
            updated_at=supplier.audit.updated_at,
            updated_by=supplier.audit.updated_by,
        )
