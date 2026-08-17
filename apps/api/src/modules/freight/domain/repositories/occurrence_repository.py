from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.occurrence import Occurrence


class OccurrenceRepository(ABC):
    """`ocorrencias` — não é um Aggregate Root próprio (D232, filho de `Trip`), sem
    `Repository[...]` genérico (mesmo padrão de `VehicleDocumentRepository`, Lote 4)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Occurrence | None: ...

    @abstractmethod
    async def add(self, aggregate: Occurrence) -> None: ...

    @abstractmethod
    async def list_page_for_trip(
        self,
        viagem_id: uuid.UUID,
        *,
        page: int,
        limit: int,
        tipo: str | None,
        status: str | None,
        gravidade: str | None,
    ) -> tuple[list[Occurrence], int]: ...
