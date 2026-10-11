from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.pricing.domain.entities.price_table import PriceTable
from modules.pricing.domain.entities.price_table_item import PriceTableItem
from modules.pricing.domain.repositories.price_table_repository import PriceTableRepository
from modules.pricing.domain.value_objects.faixa_distancia_mode import FaixaDistanciaMode
from modules.pricing.domain.value_objects.price_table_direction import PriceTableDirection
from modules.pricing.domain.value_objects.price_table_status import PriceTableStatus
from modules.pricing.domain.value_objects.price_table_unit import PriceTableUnit
from modules.pricing.infrastructure.persistence.models.price_table_model import (
    PriceTableItemModel,
    PriceTableModel,
)
from shared_kernel.domain.audit_metadata import AuditMetadata


def _table_to_entity(model: PriceTableModel) -> PriceTable:
    return PriceTable(
        id=model.id,
        nome=model.nome,
        direcao=PriceTableDirection(model.direcao),
        versao=model.versao,
        vigencia_inicio=model.vigencia_inicio,
        vigencia_fim=model.vigencia_fim,
        cliente_id=model.cliente_id,
        status=PriceTableStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em, created_by=model.criado_por,
            updated_at=model.atualizado_em, updated_by=model.atualizado_por,
        ),
    )


def _item_to_entity(model: PriceTableItemModel) -> PriceTableItem:
    return PriceTableItem(
        id=model.id,
        tabela_preco_id=model.tabela_preco_id,
        unidade_calculo=PriceTableUnit(model.unidade_calculo),
        categoria_veiculo_id=model.categoria_veiculo_id,
        origem_uf=model.origem_uf,
        destino_uf=model.destino_uf,
        faixa_distancia_min_km=model.faixa_distancia_min_km,
        faixa_distancia_max_km=model.faixa_distancia_max_km,
        faixa_modo=FaixaDistanciaMode(model.faixa_modo) if model.faixa_modo else None,
        valor=model.valor,
        valor_minimo=model.valor_minimo,
        adicional_fixo=model.adicional_fixo,
        desconto_fixo=model.desconto_fixo,
        adicional_percentual=model.adicional_percentual,
        desconto_percentual=model.desconto_percentual,
        base_percentual_descricao=model.base_percentual_descricao,
        criado_em=model.criado_em,
    )


class SqlAlchemyPriceTableRepository(PriceTableRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> PriceTable | None:
        tenant_id = get_current_tenant_id()
        stmt = select(PriceTableModel).where(PriceTableModel.id == id, PriceTableModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _table_to_entity(model) if model is not None else None

    async def add(self, aggregate: PriceTable) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(PriceTableModel, aggregate.id)
        if model is None:
            model = PriceTableModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome = aggregate.nome
        model.direcao = aggregate.direcao.value
        model.versao = aggregate.versao
        model.vigencia_inicio = aggregate.vigencia_inicio
        model.vigencia_fim = aggregate.vigencia_fim
        model.cliente_id = aggregate.cliente_id
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by

    async def list_page(
        self, *, page: int, limit: int, direcao: str | None, status: str | None, cliente_id: uuid.UUID | None
    ) -> tuple[list[PriceTable], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(PriceTableModel).where(PriceTableModel.tenant_id == tenant_id)
        if direcao is not None:
            stmt = stmt.where(PriceTableModel.direcao == direcao)
        if status is not None:
            stmt = stmt.where(PriceTableModel.status == status)
        if cliente_id is not None:
            stmt = stmt.where(PriceTableModel.cliente_id == cliente_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(PriceTableModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_table_to_entity(m) for m in models], total

    async def get_items(self, tabela_preco_id: uuid.UUID) -> list[PriceTableItem]:
        tenant_id = get_current_tenant_id()
        stmt = select(PriceTableItemModel).where(
            PriceTableItemModel.tabela_preco_id == tabela_preco_id, PriceTableItemModel.tenant_id == tenant_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_item_to_entity(m) for m in models]

    async def get_item_by_id(self, item_id: uuid.UUID) -> PriceTableItem | None:
        tenant_id = get_current_tenant_id()
        stmt = select(PriceTableItemModel).where(
            PriceTableItemModel.id == item_id, PriceTableItemModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _item_to_entity(model) if model is not None else None

    async def add_item(self, item: PriceTableItem) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            PriceTableItemModel(
                id=item.id, tenant_id=tenant_id, tabela_preco_id=item.tabela_preco_id,
                unidade_calculo=item.unidade_calculo.value, categoria_veiculo_id=item.categoria_veiculo_id,
                origem_uf=item.origem_uf, destino_uf=item.destino_uf,
                faixa_distancia_min_km=item.faixa_distancia_min_km,
                faixa_distancia_max_km=item.faixa_distancia_max_km,
                faixa_modo=item.faixa_modo.value if item.faixa_modo else None,
                valor=item.valor, valor_minimo=item.valor_minimo,
                adicional_fixo=item.adicional_fixo, desconto_fixo=item.desconto_fixo,
                adicional_percentual=item.adicional_percentual, desconto_percentual=item.desconto_percentual,
                base_percentual_descricao=item.base_percentual_descricao,
                criado_em=item.criado_em,
            )
        )

    async def delete_item(self, item_id: uuid.UUID) -> None:
        tenant_id = get_current_tenant_id()
        await self._session.execute(
            delete(PriceTableItemModel).where(
                PriceTableItemModel.id == item_id, PriceTableItemModel.tenant_id == tenant_id
            )
        )
