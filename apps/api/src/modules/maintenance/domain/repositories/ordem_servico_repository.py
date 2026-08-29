from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from shared_kernel.domain.repository import Repository


class OrdemServicoRepository(Repository[OrdemServico, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, veiculo_tracionador_id: uuid.UUID | None, tipo: str | None,
        status: str | None,
    ) -> tuple[list[OrdemServico], int]: ...
