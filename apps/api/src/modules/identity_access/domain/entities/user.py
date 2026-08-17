from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError, DomainError
from modules.identity_access.domain.value_objects.enums import UserStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class User(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `identity_access` — `docs/domain/001-cadastros.md` "Usuário". Controla sua
    própria associação a Papéis (`role_ids`, espelhando `usuarios_papeis`) — nenhum agregado
    `UsuarioPapeis` separado (`IDENTITY_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        nome: str,
        email: str,
        senha_hash: str,
        status: UserStatus,
        driver_id: uuid.UUID | None,
        employee_id: uuid.UUID | None,
        role_ids: frozenset[uuid.UUID],
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        if driver_id is not None and employee_id is not None:
            raise DomainError(
                "IDENTITY_USER_DRIVER_AND_EMPLOYEE_CONFLICT",
                "Usuário não pode estar vinculado a Motorista e Funcionário ao mesmo tempo.",
            )
        self.codigo = codigo
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.status = status
        self.driver_id = driver_id
        self.employee_id = employee_id
        self.role_ids = role_ids
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        nome: str,
        email: str,
        senha_hash: str,
        driver_id: uuid.UUID | None,
        employee_id: uuid.UUID | None,
        role_ids: frozenset[uuid.UUID],
        audit: AuditMetadata,
    ) -> "User":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            status=UserStatus.ATIVO,
            driver_id=driver_id,
            employee_id=employee_id,
            role_ids=role_ids,
            audit=audit,
        )

    def rename_and_update_email(
        self, *, nome: str | None, email: str | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        if nome is not None:
            self.nome = nome
        if email is not None:
            self.email = email
        self.audit = self.audit.touched(by=updated_by, at=now)

    def replace_roles(
        self, role_ids: frozenset[uuid.UUID], *, updated_by: uuid.UUID, now: datetime
    ) -> None:
        """`role_ids` é sempre o conjunto final, nunca incremental (`003-users.md`)."""

        self.role_ids = role_ids
        self.audit = self.audit.touched(by=updated_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("IDENTITY_USER_ALREADY_INACTIVE", "Usuário já está desativado.")
        self.status = UserStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)

    # Verificação de senha é responsabilidade da Application (LoginHandler chama
    # core.security.PasswordHasher diretamente) — o Domain nunca importa `core` (DEPENDENCY_RULES.md),
    # e "verificar senha" já é, por natureza, uma operação que depende de um serviço de
    # infraestrutura (bcrypt), não uma regra de negócio pura do agregado.
