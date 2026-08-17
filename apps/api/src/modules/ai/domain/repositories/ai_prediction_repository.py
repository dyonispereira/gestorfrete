from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_prediction import AIPrediction


class AIPredictionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIPrediction | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, categoria: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None, include_expired: bool,
    ) -> tuple[list[AIPrediction], int]:
        """`include_expired=False` filtra pelo status EFETIVO (`data_hora_validade_fim >= now()`),
        nunca pelo `status` físico gravado (D312/D425)."""
        ...

    @abstractmethod
    async def add(self, prediction: AIPrediction) -> None: ...
