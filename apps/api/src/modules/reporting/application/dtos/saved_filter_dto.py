from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from modules.reporting.domain.entities.saved_filter import SavedFilter


@dataclass(frozen=True)
class SavedFilterDTO:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    criteria: dict[str, Any]
    status: str

    @staticmethod
    def from_entity(saved_filter: SavedFilter) -> "SavedFilterDTO":
        return SavedFilterDTO(
            id=saved_filter.id, user_id=saved_filter.usuario_id, name=saved_filter.nome,
            criteria=saved_filter.criterios, status=saved_filter.status,
        )
