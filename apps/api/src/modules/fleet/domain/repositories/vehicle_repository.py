from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from modules.fleet.domain.entities.vehicle import Vehicle
from shared_kernel.domain.repository import Repository


class VehicleRepository(Repository[Vehicle, uuid.UUID]):
    @abstractmethod
    async def exists_with_placa(self, placa: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def get_by_placa_and_tenant(self, placa: str, tenant_id: uuid.UUID) -> Vehicle | None:
        """D408 — resolução explícita por tenant informado (não `get_current_tenant_id()`), usada
        pelo login Mobile ao validar um candidato (Motorista, tenant) encontrado por CPF antes de
        qualquer contexto de tenant estar em vigor."""
        ...

    @abstractmethod
    async def exists_with_renavam(self, renavam: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        search: str | None,
        placa: str | None,
        status: str | None,
        categoria_id: uuid.UUID | None,
        fabricante: str | None,
        modelo: str | None,
        ano: int | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Vehicle], int]: ...
