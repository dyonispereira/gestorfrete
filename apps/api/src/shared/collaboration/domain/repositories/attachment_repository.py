from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from shared.collaboration.domain.entities.attachment import Attachment


class AttachmentRepository(ABC):
    """Injetada por qualquer módulo dono (D186/D354) — nunca reimplementada internamente. Sem
    `Repository[Attachment, UUID]` genérico: Anexo nunca é editado depois de criado, só `create`/lê/
    `delete` (mesmo raciocínio de `VehicleCategoryRepository`, Lote 4). `delete` é hard delete real
    (`080-attachments.md`: `anexos` não tem `excluido_em` — primeira exclusão física de verdade do
    projeto, Lote 10)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Attachment | None: ...

    @abstractmethod
    async def list_for_entity(self, entidade_tipo: str, entidade_id: uuid.UUID) -> list[Attachment]: ...

    @abstractmethod
    async def count_by_file_id(self, file_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def create(self, attachment: Attachment) -> None: ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> None: ...
