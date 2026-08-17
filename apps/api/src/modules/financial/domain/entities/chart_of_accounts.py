from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import DomainError
from modules.financial.domain.value_objects.chart_of_accounts_status import ChartOfAccountsStatus
from modules.financial.domain.value_objects.chart_of_accounts_type import ChartOfAccountsType
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class ChartOfAccounts(BaseAggregateRoot[uuid.UUID]):
    """`plano_contas` — já absorve "Categoria Financeira" (D184). Hierárquica via
    `categoria_pai_id` (auto-referência); ausência de ciclo validada na Application
    (`REFERENCE_DATA_IMPLEMENTATION.md`), nunca em `CHECK` (precisaria recursão). D391 — ganha o
    bloco padrão de auditoria, ausente na DDL congelada."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo_contabil: str,
        nome: str,
        tipo: ChartOfAccountsType,
        categoria_pai_id: uuid.UUID | None,
        status: ChartOfAccountsStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo_contabil = codigo_contabil
        self.nome = nome
        self.tipo = tipo
        self.categoria_pai_id = categoria_pai_id
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo_contabil: str,
        nome: str,
        tipo: ChartOfAccountsType,
        categoria_pai_id: uuid.UUID | None,
        audit: AuditMetadata,
    ) -> "ChartOfAccounts":
        return cls(
            id=uuid.uuid4(), codigo_contabil=codigo_contabil, nome=nome, tipo=tipo,
            categoria_pai_id=categoria_pai_id, status=ChartOfAccountsStatus.ATIVO, audit=audit,
        )

    def update(
        self,
        *,
        nome: str | None,
        categoria_pai_id: uuid.UUID | None,
        status: ChartOfAccountsStatus | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if categoria_pai_id is not None:
            if categoria_pai_id == self.id:
                raise DomainError(
                    "FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED", "Uma conta não pode ser pai dela mesma."
                )
            self.categoria_pai_id = categoria_pai_id
        if status is not None:
            self.status = status
        self.audit = self.audit.touched(by=updated_by, at=now)

    def soft_delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        self.status = ChartOfAccountsStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)
