from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class Permission(BaseEntity[uuid.UUID]):
    """Platform Reference Data (D046) — `docs/domain/001-cadastros.md` "Permissão". Nunca um
    Aggregate Root com comandos de escrita nesta API (`005-permissions.md`: somente leitura para
    clientes normais) — por isso `BaseEntity`, não `BaseAggregateRoot` (nunca grava Domain Event,
    nunca muda de estado por aqui)."""

    def __init__(
        self, id: uuid.UUID, *, code: str, name: str, module: str, created_at: datetime
    ) -> None:
        super().__init__(id)
        self.code = code
        self.name = name
        self.module = module
        self.created_at = created_at
