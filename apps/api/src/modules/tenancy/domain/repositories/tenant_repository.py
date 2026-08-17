from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.tenancy.domain.entities.tenant import Tenant
from shared_kernel.domain.repository import Repository
from shared_kernel.domain.specification import Specification


class TenantRepository(Repository[Tenant, uuid.UUID]):
    @abstractmethod
    async def exists_with_cnpj(self, cnpj: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    async def find(self, specification: Specification[Tenant]) -> list[Tenant]:
        # Sem endpoint de listagem neste lote (002-tenants.md é deliberadamente singular) — mantido
        # só para satisfazer o contrato de Repository, nunca chamado por nenhum handler.
        raise NotImplementedError("Tenant não tem endpoint de listagem (002-tenants.md)")
