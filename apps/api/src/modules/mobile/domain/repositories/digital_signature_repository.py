from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.mobile.domain.entities.digital_signature import DigitalSignature


class DigitalSignatureRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> DigitalSignature | None: ...

    @abstractmethod
    async def add(self, signature: DigitalSignature) -> None: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, document_type: str | None, document_id: uuid.UUID | None
    ) -> tuple[list[DigitalSignature], int]: ...
