from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry


@dataclass(frozen=True)
class OrdemServicoStatusHistoryEntryDTO:
    id: uuid.UUID
    status: str
    usuario_id: uuid.UUID | None
    origem: str
    observacao: str | None
    data_hora: datetime

    @staticmethod
    def from_entity(entity: OrdemServicoStatusHistoryEntry) -> "OrdemServicoStatusHistoryEntryDTO":
        return OrdemServicoStatusHistoryEntryDTO(
            id=entity.id, status=entity.status, usuario_id=entity.usuario_id, origem=entity.origem,
            observacao=entity.observacao, data_hora=entity.data_hora,
        )
