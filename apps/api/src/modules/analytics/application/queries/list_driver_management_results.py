from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.management_result_dto import DriverResultDTO, build_totals
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ZERO = Decimal("0")
_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class ListDriverManagementResultsQuery(Query):
    actor: AuthenticatedActor
    date_from: date | None = None
    date_to: date | None = None


def build_driver_result(
    *, driver_id: uuid.UUID, name: str, trip_agg: TripAggregate, linked_cost: Decimal
) -> DriverResultDTO:
    totals = build_totals(trip_agg, extra_realized_cost=linked_cost)
    return DriverResultDTO(
        driver_id=driver_id, name=name,
        trip_cost_realized=trip_agg.realized_cost.quantize(_CENTS),
        linked_cost_realized=linked_cost.quantize(_CENTS),
        totals=totals,
    )


class ListDriverManagementResultsHandler(QueryHandler[ListDriverManagementResultsQuery, list[DriverResultDTO]]):
    """Dimensão Motorista do Resultado Gerencial (Lote 4). Regra explícita do usuário: nunca herda
    automaticamente todo custo do Veículo — só o custo operacional das Viagens que o Motorista
    executou (`Trip.custo_realizado`, já rateado por Viagem) + Contas a Pagar explicitamente
    vinculadas a ele (`motorista_id`, origem != VIAGEM, para não somar o que já está em
    `Trip.custo_realizado` duas vezes). Uma OS de R$30 mil sem `motorista_id` setado nunca aparece
    aqui — fica só no Veículo."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListDriverManagementResultsQuery) -> list[DriverResultDTO]:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            trip_aggs = await repo.trip_aggregates_by_driver(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            linked_costs = await repo.driver_linked_costs_realized(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            driver_ids = set(trip_aggs) | set(linked_costs)
            identities = await repo.fetch_driver_identities(
                tenant_id=query.actor.tenant_id, driver_ids=list(driver_ids)
            )

        results = [
            build_driver_result(
                driver_id=driver_id, name=identities[driver_id],
                trip_agg=trip_aggs.get(driver_id, TripAggregate(0, _ZERO, _ZERO, _ZERO, _ZERO, None)),
                linked_cost=linked_costs.get(driver_id, _ZERO),
            )
            for driver_id in driver_ids
            if driver_id in identities
        ]
        results.sort(key=lambda r: r.totals.realized_margin, reverse=True)
        return results
