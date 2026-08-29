from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.maintenance.domain.entities.aprovacao_custo import AprovacaoCusto


@dataclass(frozen=True)
class AprovacaoCustoDTO:
    id: uuid.UUID
    ordem_servico_id: uuid.UUID
    nivel: int
    decisao: str
    justificativa: str | None
    ator_id: uuid.UUID
    data_hora: datetime

    @staticmethod
    def from_entity(entity: AprovacaoCusto) -> "AprovacaoCustoDTO":
        return AprovacaoCustoDTO(
            id=entity.id, ordem_servico_id=entity.ordem_servico_id, nivel=entity.nivel,
            decisao=entity.decisao.value, justificativa=entity.justificativa, ator_id=entity.ator_id,
            data_hora=entity.data_hora,
        )
