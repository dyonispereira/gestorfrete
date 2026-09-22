from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.management_result_dto import OverviewResultDTO, build_totals
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetManagementResultOverviewQuery(Query):
    actor: AuthenticatedActor
    date_from: date | None = None
    date_to: date | None = None


class GetManagementResultOverviewHandler(QueryHandler[GetManagementResultOverviewQuery, OverviewResultDTO]):
    """Visão Geral do Resultado Gerencial (Lote 4). Custo Realizado da empresa inclui Manutenção +
    Outros Custos fora de Viagem de toda a frota, não só o que as Viagens consumiram — a mesma
    lógica de "Resultado Total do Veículo" aplicada em escala de tenant, para que o topo do painel
    nunca esconda gasto fora de viagem. `other_costs_realized_total` é uma soma única (nunca a soma
    de dois agrupamentos que podem compartilhar a mesma Conta a Pagar — ver a nota no Repository)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetManagementResultOverviewQuery) -> OverviewResultDTO:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            trip_agg = await repo.trip_overview(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            maintenance_by_vehicle = await repo.maintenance_realized_by_vehicle(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            other_costs_total = await repo.other_costs_realized_total(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )

        maintenance_total = sum(maintenance_by_vehicle.values(), start=Decimal("0"))
        totals = build_totals(trip_agg, extra_realized_cost=maintenance_total + other_costs_total)
        return OverviewResultDTO(
            totals=totals, maintenance_cost_realized=maintenance_total, other_costs_realized=other_costs_total,
        )
