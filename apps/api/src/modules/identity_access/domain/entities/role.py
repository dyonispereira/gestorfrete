from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Role(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `identity_access` — `docs/domain/001-cadastros.md` "Papel" ("Perfil" no
    vocabulário de negócio, D028). Controla seu próprio conjunto de Permissões
    (`permission_ids`, espelhando `papel_permissao`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        nome: str,
        descricao: str | None,
        permission_ids: frozenset[uuid.UUID],
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nome = nome
        self.descricao = descricao
        self.permission_ids = permission_ids
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        nome: str,
        descricao: str | None,
        permission_ids: frozenset[uuid.UUID],
        audit: AuditMetadata,
    ) -> "Role":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            permission_ids=permission_ids,
            audit=audit,
        )

    def update(
        self,
        *,
        nome: str | None,
        descricao: str | None,
        permission_ids: frozenset[uuid.UUID] | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if descricao is not None:
            self.descricao = descricao
        if permission_ids is not None:
            self.permission_ids = permission_ids
        self.audit = self.audit.touched(by=updated_by, at=now)

    def soft_delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)
