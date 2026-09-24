from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.freight.domain.entities.manifest import Manifest


class ManifestRepository(ABC):
    """`romaneios`/`itens_carga` — não é um Aggregate Root próprio, filho do agregado Viagem."""

    @abstractmethod
    async def exists_for_trip(self, viagem_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def create(self, manifest: Manifest) -> None:
        """Escreve o Romaneio e todos os seus Itens de Carga."""
        ...
