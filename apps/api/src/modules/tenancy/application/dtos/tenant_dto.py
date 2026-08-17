from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.tenancy.domain.entities.tenant import Tenant


@dataclass(frozen=True)
class TenantDTO:
    """Fronteira entre Application e Interfaces (`APPLICATION_LAYER.md`) — nunca o mesmo objeto que
    o schema Pydantic HTTP nem o modelo SQLAlchemy."""

    id: uuid.UUID
    codigo: str
    razao_social: str
    cnpj: str
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(tenant: Tenant) -> "TenantDTO":
        return TenantDTO(
            id=tenant.id,
            codigo=tenant.codigo,
            razao_social=tenant.razao_social,
            cnpj=tenant.cnpj,
            status=tenant.status.value,
            created_at=tenant.audit.created_at,
            created_by=tenant.audit.created_by,
            updated_at=tenant.audit.updated_at,
            updated_by=tenant.audit.updated_by,
        )
