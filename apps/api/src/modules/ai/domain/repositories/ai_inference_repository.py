from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from modules.ai.domain.entities.ai_inference import AIInference


class AIInferenceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIInference | None: ...

    @abstractmethod
    async def list_page(
        self, *, cursor_data_hora: datetime | None, cursor_id: uuid.UUID | None, limit: int,
        modelo_ia_id: uuid.UUID | None, status: str | None, origem: str | None,
        started_at_from: datetime | None, started_at_to: datetime | None,
    ) -> list[AIInference]: ...

    @abstractmethod
    async def add(self, inference: AIInference) -> None: ...
