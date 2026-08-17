from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.identity_access.domain.entities.role import Role
from shared_kernel.domain.repository import Repository


class RoleRepository(Repository[Role, uuid.UUID]):
    @abstractmethod
    async def get_many(self, ids: frozenset[uuid.UUID]) -> list[Role]: ...

    @abstractmethod
    async def exists_with_name(self, nome: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def list_page(self, *, page: int, limit: int, search: str | None) -> tuple[list[Role], int]: ...

    @abstractmethod
    async def is_assigned_to_any_user(self, role_id: uuid.UUID) -> bool:
        """Suporta `IDENTITY_ROLE_IN_USE` (`004-roles.md`)."""
