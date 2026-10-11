from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.trip_price_application import TripPriceApplication
from modules.freight.domain.repositories.trip_price_application_repository import TripPriceApplicationRepository
from modules.freight.infrastructure.persistence.models.trip_price_application_model import (
    TripPriceApplicationModel,
)


def _to_entity(model: TripPriceApplicationModel) -> TripPriceApplication:
    return TripPriceApplication(
        id=model.id,
        viagem_id=model.viagem_id,
        tabela_preco_id=model.tabela_preco_id,
        item_tabela_preco_id=model.item_tabela_preco_id,
        tabela_preco_versao=model.tabela_preco_versao,
        direcao=model.direcao,
        unidade_calculo=model.unidade_calculo,
        quantidade_utilizada=model.quantidade_utilizada,
        base_percentual_valor=model.base_percentual_valor,
        tarifa_aplicada=model.tarifa_aplicada,
        valor_minimo_aplicado=model.valor_minimo_aplicado,
        adicional_fixo_aplicado=model.adicional_fixo_aplicado,
        desconto_fixo_aplicado=model.desconto_fixo_aplicado,
        adicional_percentual_aplicado=model.adicional_percentual_aplicado,
        desconto_percentual_aplicado=model.desconto_percentual_aplicado,
        valor_calculado_bruto=model.valor_calculado_bruto,
        valor_final=model.valor_final,
        aplicado_em=model.aplicado_em,
        aplicado_por=model.aplicado_por,
        removido_em=model.removido_em,
        removido_por=model.removido_por,
    )


class SqlAlchemyTripPriceApplicationRepository(TripPriceApplicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, application: TripPriceApplication) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            TripPriceApplicationModel(
                id=application.id, tenant_id=tenant_id, viagem_id=application.viagem_id,
                tabela_preco_id=application.tabela_preco_id, item_tabela_preco_id=application.item_tabela_preco_id,
                tabela_preco_versao=application.tabela_preco_versao, direcao=application.direcao,
                unidade_calculo=application.unidade_calculo, quantidade_utilizada=application.quantidade_utilizada,
                base_percentual_valor=application.base_percentual_valor, tarifa_aplicada=application.tarifa_aplicada,
                valor_minimo_aplicado=application.valor_minimo_aplicado,
                adicional_fixo_aplicado=application.adicional_fixo_aplicado,
                desconto_fixo_aplicado=application.desconto_fixo_aplicado,
                adicional_percentual_aplicado=application.adicional_percentual_aplicado,
                desconto_percentual_aplicado=application.desconto_percentual_aplicado,
                valor_calculado_bruto=application.valor_calculado_bruto, valor_final=application.valor_final,
                aplicado_em=application.aplicado_em, aplicado_por=application.aplicado_por,
                removido_em=application.removido_em, removido_por=application.removido_por,
            )
        )

    async def get_active_for_trip(self, viagem_id: uuid.UUID) -> TripPriceApplication | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TripPriceApplicationModel).where(
            TripPriceApplicationModel.viagem_id == viagem_id,
            TripPriceApplicationModel.tenant_id == tenant_id,
            TripPriceApplicationModel.removido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_id(self, id: uuid.UUID) -> TripPriceApplication | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TripPriceApplicationModel).where(
            TripPriceApplicationModel.id == id, TripPriceApplicationModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def mark_removed(self, application: TripPriceApplication) -> None:
        tenant_id = get_current_tenant_id()
        stmt = select(TripPriceApplicationModel).where(
            TripPriceApplicationModel.id == application.id, TripPriceApplicationModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one()
        model.removido_em = application.removido_em
        model.removido_por = application.removido_por
