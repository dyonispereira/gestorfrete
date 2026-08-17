from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.identity_access.domain.entities.user import User
from shared_kernel.domain.repository import Repository


class UserRepository(Repository[User, uuid.UUID]):
    @abstractmethod
    async def get_by_email(self, email: str) -> tuple[User, uuid.UUID] | None:
        """Retorna `(User, tenant_id)` — o único método deste bounded context que resolve um
        Usuário **sem** um tenant já em contexto (necessário para o login, D208's única exceção
        documentada: o próprio ponto de entrada precisa descobrir o tenant a partir do e-mail)."""

    @abstractmethod
    async def exists_with_email(self, email: str) -> bool: ...

    @abstractmethod
    async def get_by_driver_id_and_tenant(self, driver_id: uuid.UUID, tenant_id: uuid.UUID) -> User | None:
        """D408 — login Mobile por CPF+Placa já resolveu explicitamente qual tenant antes de chegar
        aqui; usa o `tenant_id` recebido como parâmetro, nunca `get_current_tenant_id()` (ainda não
        há contexto de tenant em vigor neste ponto do fluxo)."""

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, status: str | None, role_id: uuid.UUID | None, search: str | None
    ) -> tuple[list[User], int]: ...

    @abstractmethod
    async def count_active_admins(self, *, excluding_user_id: uuid.UUID, admin_role_ids: frozenset[uuid.UUID]) -> int:
        """Suporta a regra `IDENTITY_CANNOT_DEACTIVATE_LAST_ADMIN` (`003-users.md`)."""

    @abstractmethod
    async def exists_active_linked_to_employee(self, employee_id: uuid.UUID) -> bool:
        """Suporta `IDENTITY_EMPLOYEE_LINKED_TO_ACTIVE_USER` (`010-employees.md`, Sprint 11
        Lote 3)."""
