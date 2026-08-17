from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class _StatusHistoryEntryLike(Protocol):
    """`id` é `@property` só-leitura em `BaseEntity` — declarado aqui como `property` também,
    nunca um atributo mutável, para o Protocol casar estruturalmente com `CteStatusHistoryEntry`/
    `MdfeStatusHistoryEntry`/`CiotStatusHistoryEntry`."""

    @property
    def id(self) -> uuid.UUID: ...

    status: str
    usuario_id: uuid.UUID | None
    origem: str
    observacao: str | None
    data_hora: datetime


@dataclass(frozen=True)
class StatusHistoryEntryDTO:
    """DTO compartilhado por CT-e/MDF-e/CIOT status-history (D284 — mesmos campos padrão nos
    três)."""

    id: uuid.UUID
    status: str
    user_id: uuid.UUID | None
    origin: str
    notes: str | None
    occurred_at: datetime

    @staticmethod
    def from_entity(entity: _StatusHistoryEntryLike) -> "StatusHistoryEntryDTO":
        return StatusHistoryEntryDTO(
            id=entity.id, status=entity.status, user_id=entity.usuario_id, origin=entity.origem,
            notes=entity.observacao, occurred_at=entity.data_hora,
        )
