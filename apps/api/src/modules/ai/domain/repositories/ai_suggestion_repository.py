from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_suggestion import AISuggestion


class AISuggestionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AISuggestion | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, categoria: str | None, entidade_alvo_tipo: str | None,
        entidade_alvo_id: uuid.UUID | None, status: str | None,
    ) -> tuple[list[AISuggestion], int]: ...

    @abstractmethod
    async def add(self, suggestion: AISuggestion) -> None: ...
