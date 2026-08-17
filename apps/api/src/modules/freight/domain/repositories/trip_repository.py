from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import date
from typing import Any

from modules.freight.domain.entities.trip import Trip
from shared_kernel.domain.repository import Repository


class TripRepository(Repository[Trip, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status_operacional: str | None,
        status_fiscal: str | None,
        status_financeiro: str | None,
        motorista_id: uuid.UUID | None,
        veiculo_id: uuid.UUID | None,
        cliente_id: uuid.UUID | None,
        data_programada: date | None,
        codigo: str | None,
    ) -> tuple[list[Trip], int]: ...

    @abstractmethod
    async def get_client_snapshot(self, cliente_id: uuid.UUID) -> dict[str, Any] | None:
        """Leitura cross-module de `crm.Client` (D356, aceita) — só para montar `cliente_snapshot`
        na criação da Viagem, nunca para validar regra de negócio de `crm`."""
        ...

    @abstractmethod
    async def client_exists(self, cliente_id: uuid.UUID) -> bool: ...
