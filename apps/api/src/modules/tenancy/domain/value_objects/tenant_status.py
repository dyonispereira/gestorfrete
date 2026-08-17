from __future__ import annotations

from enum import StrEnum


class TenantStatus(StrEnum):
    """Espelha `tenants_status_enum` (relational/001-core.md). Nunca alterado por este bounded
    context nesta etapa — governado pelo fluxo de assinatura/cobrança (D-alinhado a
    docs/api/002-tenants.md)."""

    TRIAL = "TRIAL"
    ATIVO = "ATIVO"
    SUSPENSO = "SUSPENSO"
    CANCELADO = "CANCELADO"
