from __future__ import annotations

import uuid
from datetime import datetime

from modules.financial.domain.value_objects.bank_account_status import BankAccountStatus
from modules.financial.domain.value_objects.bank_account_type import BankAccountType
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class BankAccount(BaseAggregateRoot[uuid.UUID]):
    """`contas_bancarias` (D189). `numero_conta`/`tipo` imutáveis após criação (Atributo Crítico,
    D077-style) — troca é evento raro/sensível, vira conta nova. D391 — ganha o bloco padrão de
    auditoria, ausente na DDL congelada."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        banco: str,
        agencia: str,
        numero_conta: str,
        tipo: BankAccountType,
        status: BankAccountStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.banco = banco
        self.agencia = agencia
        self.numero_conta = numero_conta
        self.tipo = tipo
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls, *, banco: str, agencia: str, numero_conta: str, tipo: BankAccountType, audit: AuditMetadata
    ) -> "BankAccount":
        return cls(
            id=uuid.uuid4(), banco=banco, agencia=agencia, numero_conta=numero_conta, tipo=tipo,
            status=BankAccountStatus.ATIVA, audit=audit,
        )

    def update(
        self, *, banco: str | None, agencia: str | None, status: BankAccountStatus | None,
        updated_by: uuid.UUID, now: datetime,
    ) -> None:
        if banco is not None:
            self.banco = banco
        if agencia is not None:
            self.agencia = agencia
        if status is not None:
            self.status = status
        self.audit = self.audit.touched(by=updated_by, at=now)

    def soft_delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        self.status = BankAccountStatus.INATIVA
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)
