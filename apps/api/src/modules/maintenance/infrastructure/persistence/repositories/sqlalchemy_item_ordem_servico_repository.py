from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.item_ordem_servico import ItemOrdemServico
from modules.maintenance.domain.repositories.item_ordem_servico_repository import ItemOrdemServicoRepository
from modules.maintenance.domain.value_objects.item_ordem_servico_categoria_custo import (
    ItemOrdemServicoCategoriaCusto,
)
from modules.maintenance.infrastructure.persistence.models.item_ordem_servico_model import ItemOrdemServicoModel


def _to_entity(model: ItemOrdemServicoModel) -> ItemOrdemServico:
    return ItemOrdemServico(
        id=model.id, ordem_servico_id=model.ordem_servico_id,
        categoria_custo=ItemOrdemServicoCategoriaCusto(model.categoria_custo), descricao=model.descricao,
        peca_estoque_id=model.peca_estoque_id, quantidade=model.quantidade, valor_unitario=model.valor_unitario,
    )


class SqlAlchemyItemOrdemServicoRepository(ItemOrdemServicoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: ItemOrdemServico) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ItemOrdemServicoModel, item.id)
        if model is None:
            model = ItemOrdemServicoModel(id=item.id, tenant_id=tenant_id)
            self._session.add(model)
        model.ordem_servico_id = item.ordem_servico_id
        model.categoria_custo = item.categoria_custo.value
        model.descricao = item.descricao
        model.peca_estoque_id = item.peca_estoque_id
        model.quantidade = item.quantidade
        model.valor_unitario = item.valor_unitario
        await self._session.flush()

    async def list_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> list[ItemOrdemServico]:
        tenant_id = get_current_tenant_id()
        stmt = select(ItemOrdemServicoModel).where(
            ItemOrdemServicoModel.tenant_id == tenant_id, ItemOrdemServicoModel.ordem_servico_id == ordem_servico_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
