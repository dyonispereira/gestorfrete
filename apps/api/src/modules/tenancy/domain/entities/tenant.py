from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import DomainError
from modules.tenancy.domain.value_objects.tenant_status import TenantStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Tenant(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `tenancy` — implementação física de `docs/domain/010-administracao.md`
    "Tenant". Escopo desta etapa: só o que `docs/api/002-tenants.md` (congelado) expõe —
    `status` nunca tem um método de mudança aqui, é governado pelo fluxo de assinatura/cobrança,
    ainda não implementado.
    """

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        versao: int,
        razao_social: str,
        cnpj: str,
        status: TenantStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.versao = versao
        self.razao_social = razao_social
        self.cnpj = cnpj
        self.status = status
        self.audit = audit

    def update_company_data(
        self, *, razao_social: str | None, cnpj: str | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        """Único método de escrita deste agregado nesta etapa (`002-tenants.md`'s `PATCH /tenant`).
        `PATCH` é sempre parcial — campos `None` (não enviados) não alteram o valor atual.
        """

        if razao_social is not None and not razao_social.strip():
            raise DomainError("TENANCY_RAZAO_SOCIAL_EMPTY", "Razão social não pode ser vazia.")
        if razao_social is not None:
            self.razao_social = razao_social
        if cnpj is not None:
            self.cnpj = cnpj
        self.audit = self.audit.touched(by=updated_by, at=now)
