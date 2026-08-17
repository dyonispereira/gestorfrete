from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.financial.domain.entities.chart_of_accounts import ChartOfAccounts
from shared_kernel.domain.repository import Repository


class ChartOfAccountsRepository(Repository[ChartOfAccounts, uuid.UUID]):
    @abstractmethod
    async def exists_with_codigo(self, codigo_contabil: str, *, excluding_id: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def has_active_children(self, parent_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def is_descendant_of(self, candidate_ancestor_id: uuid.UUID, node_id: uuid.UUID) -> bool:
        """Percorre `categoria_pai_id` a partir de `node_id` até a raiz — verdadeiro se
        `candidate_ancestor_id` aparecer no caminho (detecção de ciclo, `034-chart-of-
        accounts.md`)."""
        ...

    @abstractmethod
    async def is_referenced_by_payables(self, id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, tipo: str | None, parent_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[ChartOfAccounts], int]: ...
