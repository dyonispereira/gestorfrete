from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.documents.domain.entities.correction_letter import CorrectionLetter


class CorrectionLetterRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> CorrectionLetter | None: ...

    @abstractmethod
    async def add(self, letter: CorrectionLetter) -> None: ...

    @abstractmethod
    async def list_for_cte(self, cte_id: uuid.UUID) -> list[CorrectionLetter]: ...

    @abstractmethod
    async def next_sequence_number(self, cte_id: uuid.UUID) -> int: ...
