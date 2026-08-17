from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.identity_access.domain.entities.permission import Permission


class PermissionRepository(ABC):
    """Não estende `shared_kernel.domain.repository.Repository` — Permission não é um Aggregate
    Root (`domain/entities/permission.py`), e é Platform Reference Data sem `tenant_id`
    (`get_by_id` de um `Repository[T]` comum implicaria o filtro de tenant que aqui não existe)."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Permission | None: ...

    @abstractmethod
    async def get_by_codes(self, codes: list[str]) -> list[Permission]: ...

    @abstractmethod
    async def get_by_ids(self, ids: frozenset[uuid.UUID]) -> list[Permission]: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, module: str | None, search: str | None
    ) -> tuple[list[Permission], int]: ...
