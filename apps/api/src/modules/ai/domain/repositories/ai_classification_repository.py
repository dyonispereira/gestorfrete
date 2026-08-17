from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_classification import AIClassification


class AIClassificationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIClassification | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, tipo_classificacao: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None,
    ) -> tuple[list[AIClassification], int]: ...

    @abstractmethod
    async def add(self, classification: AIClassification) -> None: ...
