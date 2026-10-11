from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.pricing.domain.entities.price_table import PriceTable
from modules.pricing.domain.entities.price_table_item import PriceTableItem
from shared_kernel.domain.repository import Repository
from shared_kernel.domain.specification import Specification


class PriceTableRepository(Repository[PriceTable, uuid.UUID]):
    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, direcao: str | None, status: str | None, cliente_id: uuid.UUID | None
    ) -> tuple[list[PriceTable], int]: ...

    @abstractmethod
    async def get_items(self, tabela_preco_id: uuid.UUID) -> list[PriceTableItem]: ...

    @abstractmethod
    async def get_item_by_id(self, item_id: uuid.UUID) -> PriceTableItem | None: ...

    @abstractmethod
    async def add_item(self, item: PriceTableItem) -> None: ...

    @abstractmethod
    async def delete_item(self, item_id: uuid.UUID) -> None: ...

    async def find(self, specification: Specification[PriceTable]) -> list[PriceTable]:
        raise NotImplementedError("Use list_page — filtros de PriceTable são resolvidos via SQL")
