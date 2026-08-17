from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.ai.domain.entities.ai_model import AIModel


@dataclass(frozen=True)
class AIModelDTO:
    id: uuid.UUID
    name: str
    type: str
    version: str
    logical_provider: str
    capability: str
    max_context: int | None
    status: str

    @staticmethod
    def from_entity(model: AIModel) -> "AIModelDTO":
        return AIModelDTO(
            id=model.id, name=model.nome, type=model.tipo.value, version=model.versao,
            logical_provider=model.fornecedor_logico.value, capability=model.capacidade,
            max_context=model.contexto_maximo, status=model.status.value,
        )
