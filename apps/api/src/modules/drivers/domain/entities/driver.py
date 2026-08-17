from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError, DomainError
from modules.drivers.domain.value_objects.employment_type import EmploymentType
from modules.drivers.domain.value_objects.fitness_status import FitnessStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Driver(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `drivers` — `docs/domain/001-cadastros.md` "Motorista". `fitness_status`
    só muda via `block()`/`unblock()` — nunca um setter direto (`DRIVER_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        nome: str,
        cpf: str,
        telefone: str | None,
        email: str | None,
        employment_type: EmploymentType,
        fitness_status: FitnessStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nome = nome
        self.cpf = cpf
        self.telefone = telefone
        self.email = email
        self.employment_type = employment_type
        self.fitness_status = fitness_status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        nome: str,
        cpf: str,
        telefone: str | None,
        email: str | None,
        employment_type: EmploymentType,
        audit: AuditMetadata,
    ) -> "Driver":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            nome=nome,
            cpf=cpf,
            telefone=telefone,
            email=email,
            employment_type=employment_type,
            fitness_status=FitnessStatus.APTO,
            audit=audit,
        )

    def update(
        self, *, nome: str | None, telefone: str | None, email: str | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        if nome is not None:
            self.nome = nome
        if telefone is not None:
            self.telefone = telefone
        if email is not None:
            self.email = email
        self.audit = self.audit.touched(by=updated_by, at=now)

    def block(self, *, blocked_by: uuid.UUID, now: datetime) -> None:
        if self.fitness_status == FitnessStatus.BLOQUEADO:
            raise DomainError("DRIVERS_ALREADY_BLOCKED", "Motorista já está bloqueado.")
        self.fitness_status = FitnessStatus.BLOQUEADO
        self.audit = self.audit.touched(by=blocked_by, at=now)

    def unblock(self, *, unblocked_by: uuid.UUID, now: datetime) -> None:
        if self.fitness_status == FitnessStatus.APTO:
            raise DomainError("DRIVERS_ALREADY_UNBLOCKED", "Motorista já está apto.")
        self.fitness_status = FitnessStatus.APTO
        self.audit = self.audit.touched(by=unblocked_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("DRIVERS_DRIVER_ALREADY_INACTIVE", "Motorista já está inativo.")
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)
