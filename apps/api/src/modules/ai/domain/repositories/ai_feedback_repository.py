from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_feedback import AIFeedback


class AIFeedbackRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIFeedback | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, saida_ia_tipo: str | None, saida_ia_id: uuid.UUID | None,
        resultado: str | None,
    ) -> tuple[list[AIFeedback], int]: ...

    @abstractmethod
    async def add(self, feedback: AIFeedback) -> None: ...
