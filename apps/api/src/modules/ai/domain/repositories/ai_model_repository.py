from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.ai.domain.entities.ai_model import AIModel


class AIModelRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> AIModel | None: ...

    @abstractmethod
    async def exists_with_name_and_version(self, nome: str, versao: str) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, tipo: str | None, fornecedor_logico: str | None, status: str | None,
    ) -> tuple[list[AIModel], int]: ...

    @abstractmethod
    async def add(self, model: AIModel) -> None: ...
