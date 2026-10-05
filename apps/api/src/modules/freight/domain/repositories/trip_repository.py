from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import date
from typing import Any

from modules.freight.domain.entities.trip import Trip
from shared_kernel.domain.repository import Repository


class TripRepository(Repository[Trip, uuid.UUID]):
    @abstractmethod
    async def get_by_id_for_update(self, id: uuid.UUID) -> Trip | None:
        """`SELECT ... FOR UPDATE` na linha da Viagem — mesmo padrão de
        `FiscalConfigurationRepository.get_for_tenant_locked()` (D399). Hotfix P0 Fase 2 (Gate 6) —
        `get_by_id()` comum nunca bloqueia, então duas transações concorrentes podiam ambas ler a
        Viagem como `LIBERADA` antes de qualquer uma commitar, e a segunda nunca relia o estado
        real ao finalmente prosseguir, duplicando o despacho/CT-e. Reservado para comandos mutáveis
        críticos que precisam serializar contra escrita concorrente na mesma Viagem — não para todo
        `get_by_id()`, que continua sem lock para leituras comuns."""
        ...

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
