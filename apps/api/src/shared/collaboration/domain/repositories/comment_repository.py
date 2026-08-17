from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from shared.collaboration.domain.entities.comment import Comment


class CommentRepository(ABC):
    """Injetada por qualquer módulo dono (D186/D354) — nunca reimplementada internamente. `update`
    só altera `texto`/`visivel_cliente` (`081-comments.md`: só o próprio autor, reforçado no
    Handler, nunca aqui). `delete` é hard delete real (`comentarios` não tem `excluido_em`, mesma
    disciplina de `AttachmentRepository`, Lote 10)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Comment | None: ...

    @abstractmethod
    async def list_for_entity(self, entidade_tipo: str, entidade_id: uuid.UUID) -> list[Comment]: ...

    @abstractmethod
    async def create(self, comment: Comment) -> None: ...

    @abstractmethod
    async def update(self, comment: Comment) -> None: ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> None: ...
