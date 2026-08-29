from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from modules.maintenance.domain.entities.checklist import Checklist


@dataclass(frozen=True)
class ChecklistDTO:
    id: uuid.UUID
    codigo: str
    tipo: str
    referencia_tipo: str
    referencia_id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    motorista_id: uuid.UUID | None
    itens: list[dict[str, Any]]
    status: str
    checklist_reprovado_id: uuid.UUID | None
    criado_em: datetime
    atualizado_em: datetime

    @staticmethod
    def from_entity(entity: Checklist) -> "ChecklistDTO":
        return ChecklistDTO(
            id=entity.id, codigo=entity.codigo, tipo=entity.tipo.value, referencia_tipo=entity.referencia_tipo.value,
            referencia_id=entity.referencia_id, veiculo_tracionador_id=entity.veiculo_tracionador_id,
            motorista_id=entity.motorista_id, itens=entity.itens, status=entity.status.value,
            checklist_reprovado_id=entity.checklist_reprovado_id, criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em,
        )
