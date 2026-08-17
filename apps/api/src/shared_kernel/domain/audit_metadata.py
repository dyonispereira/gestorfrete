from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditMetadata:
    """Os atributos universais de toda entidade de negócio (D069) — mesmos quatro campos expostos
    publicamente por `components/schemas.md#AuditMetadata` (`created_at`/`created_by`/
    `updated_at`/`updated_by`), mais os dois de soft delete (D001/D177), que existem na tabela
    física mas nunca são serializados para a API (D343 — exclusão é um padrão de leitura, não um
    detalhe que o cliente precisa ver).
    """

    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_deleted(self, *, by: uuid.UUID, at: datetime) -> "AuditMetadata":
        if self.is_deleted:
            raise ValueError("Already soft-deleted")
        return AuditMetadata(
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=at,
            updated_by=by,
            deleted_at=at,
            deleted_by=by,
        )

    def touched(self, *, by: uuid.UUID | None, at: datetime) -> "AuditMetadata":
        return AuditMetadata(
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=at,
            updated_by=by,
            deleted_at=self.deleted_at,
            deleted_by=self.deleted_by,
        )
