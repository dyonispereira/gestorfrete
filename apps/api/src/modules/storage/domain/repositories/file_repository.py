from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.storage.domain.entities.file import File


class FileRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> File | None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, mime_type: str | None, origin: str | None, status: str
    ) -> tuple[list[File], int]: ...

    @abstractmethod
    async def list_versions(self, file_id: uuid.UUID) -> list[File]: ...

    @abstractmethod
    async def add(self, file: File) -> None: ...
