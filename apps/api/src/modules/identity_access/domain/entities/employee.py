from __future__ import annotations

import uuid
from datetime import date, datetime

from core.exceptions.base import ConflictError
from modules.identity_access.domain.value_objects.employee_status import EmployeeStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Employee(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `identity_access` — `docs/domain/001-cadastros.md` "Funcionário" (D196).
    Nunca ganha uma coluna `usuario_id` — o vínculo é sempre do lado de `Usuário`
    (`usuarios.funcionario_id`, já implementado no Lote 2), `EMPLOYEE_IMPLEMENTATION.md`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        nome: str,
        cargo: str,
        data_admissao: date | None,
        status: EmployeeStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nome = nome
        self.cargo = cargo
        self.data_admissao = data_admissao
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls, *, codigo: str, nome: str, cargo: str, data_admissao: date | None, audit: AuditMetadata
    ) -> "Employee":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            nome=nome,
            cargo=cargo,
            data_admissao=data_admissao,
            status=EmployeeStatus.ATIVO,
            audit=audit,
        )

    def update(
        self, *, nome: str | None, cargo: str | None, data_admissao: date | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        if nome is not None:
            self.nome = nome
        if cargo is not None:
            self.cargo = cargo
        if data_admissao is not None:
            self.data_admissao = data_admissao
        self.audit = self.audit.touched(by=updated_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("IDENTITY_EMPLOYEE_ALREADY_INACTIVE", "Funcionário já está inativo.")
        self.status = EmployeeStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)
