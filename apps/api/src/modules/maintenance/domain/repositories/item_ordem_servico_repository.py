from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.maintenance.domain.entities.item_ordem_servico import ItemOrdemServico


class ItemOrdemServicoRepository(ABC):
    @abstractmethod
    async def add(self, item: ItemOrdemServico) -> None: ...

    @abstractmethod
    async def list_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> list[ItemOrdemServico]: ...
