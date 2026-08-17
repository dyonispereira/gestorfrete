from __future__ import annotations

import uuid
from datetime import datetime

from modules.financial.domain.value_objects.cost_center_status import CostCenterStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class CostCenter(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `financial` — `docs/domain/001-cadastros.md` "Centro de Custo". Cadastro
    mestre puro (D090): nunca ganha campo de saldo/indicador/valor acumulado
    (`COST_CENTER_IMPLEMENTATION.md`). `filial_id` é aceito e armazenado, mas nunca validado contra
    uma tabela `Filial` que ainda não existe (D355)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        codigo_contabil: str,
        nome: str,
        filial_id: uuid.UUID | None,
        status: CostCenterStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.codigo_contabil = codigo_contabil
        self.nome = nome
        self.filial_id = filial_id
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls, *, codigo: str, codigo_contabil: str, nome: str, filial_id: uuid.UUID | None, audit: AuditMetadata
    ) -> "CostCenter":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            codigo_contabil=codigo_contabil,
            nome=nome,
            filial_id=filial_id,
            status=CostCenterStatus.ATIVO,
            audit=audit,
        )

    def update(
        self,
        *,
        nome: str | None,
        filial_id: uuid.UUID | None,
        status: CostCenterStatus | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if filial_id is not None:
            self.filial_id = filial_id
        if status is not None:
            self.status = status
        self.audit = self.audit.touched(by=updated_by, at=now)
