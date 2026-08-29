from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.maintenance.domain.entities.aprovacao_custo import AprovacaoCusto


class AprovacaoCustoRepository(ABC):
    @abstractmethod
    async def add(self, aprovacao: AprovacaoCusto) -> None: ...

    @abstractmethod
    async def list_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> list[AprovacaoCusto]: ...
