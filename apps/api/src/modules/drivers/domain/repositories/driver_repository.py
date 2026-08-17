from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.drivers.domain.entities.driver import Driver
from shared_kernel.domain.repository import Repository


class DriverRepository(Repository[Driver, uuid.UUID]):
    @abstractmethod
    async def exists_with_cpf(self, cpf: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> Driver | None: ...

    @abstractmethod
    async def list_by_cpf_across_tenants(self, cpf: str) -> list[tuple[Driver, uuid.UUID]]:
        """D408 — exceção tenant-livre, mesma natureza documentada de `UserRepository.get_by_email`:
        login Mobile por CPF+Placa precisa descobrir o tenant antes de qualquer contexto de tenant
        existir. `cpf` é único só por tenant (`uq_motoristas_tenant_id_cpf`), nunca globalmente —
        por isso retorna uma lista, não um único resultado."""
        ...

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        employment_type: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Driver], int]: ...
