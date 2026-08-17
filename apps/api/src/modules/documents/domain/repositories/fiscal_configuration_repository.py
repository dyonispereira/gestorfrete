from __future__ import annotations

from abc import ABC, abstractmethod

from modules.documents.domain.entities.fiscal_configuration import FiscalConfiguration


class FiscalConfigurationRepository(ABC):
    @abstractmethod
    async def get_for_tenant(self) -> FiscalConfiguration | None: ...

    @abstractmethod
    async def get_for_tenant_locked(self) -> FiscalConfiguration | None:
        """D399 — `SELECT ... FOR UPDATE` na linha da configuração do tenant. Chamado sempre dentro
        da mesma transação que cria um CT-e/MDF-e, garantindo numeração atômica mesmo sob emissões
        concorrentes."""
        ...

    @abstractmethod
    async def add(self, configuration: FiscalConfiguration) -> None: ...
