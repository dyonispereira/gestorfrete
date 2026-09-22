from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.management_result_dto import VehicleResultDTO, build_totals
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ZERO = Decimal("0")
_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class ListVehicleManagementResultsQuery(Query):
    actor: AuthenticatedActor
    date_from: date | None = None
    date_to: date | None = None


def build_vehicle_result(
    *,
    vehicle_id: uuid.UUID,
    plate: str,
    model: str,
    trip_agg: TripAggregate,
    maintenance_predicted: Decimal,
    maintenance_realized: Decimal,
    other_realized: Decimal,
) -> VehicleResultDTO:
    """Função pura, reusada pela listagem e pelo drill-down — Resultado Operacional de Viagens
    (só a Viagem) vs. Resultado Total (`totals`, inclui Manutenção + Outros Custos do ativo)."""

    operational_result = trip_agg.realized_revenue - trip_agg.realized_cost
    operational_margin_pct = (
        (operational_result / trip_agg.realized_revenue * Decimal("100")).quantize(_CENTS, rounding=ROUND_HALF_UP)
        if trip_agg.realized_revenue != _ZERO
        else None
    )
    totals = build_totals(
        trip_agg, extra_realized_cost=maintenance_realized + other_realized, extra_predicted_cost=maintenance_predicted
    )
    return VehicleResultDTO(
        vehicle_id=vehicle_id, plate=plate, model=model,
        trip_cost_realized=trip_agg.realized_cost.quantize(_CENTS, rounding=ROUND_HALF_UP),
        maintenance_cost_predicted=maintenance_predicted.quantize(_CENTS, rounding=ROUND_HALF_UP),
        maintenance_cost_realized=maintenance_realized.quantize(_CENTS, rounding=ROUND_HALF_UP),
        other_costs_realized=other_realized.quantize(_CENTS, rounding=ROUND_HALF_UP),
        operational_result=operational_result.quantize(_CENTS, rounding=ROUND_HALF_UP),
        operational_margin_pct=operational_margin_pct,
        totals=totals,
    )


class ListVehicleManagementResultsHandler(
    QueryHandler[ListVehicleManagementResultsQuery, list[VehicleResultDTO]]
):
    """Dimensão Veículo do Resultado Gerencial (Lote 4) — a única que soma custo fora de Viagem
    (Manutenção via Ordem de Serviço, Outros Custos tagueados direto no Veículo). Ranking (sem
    paginação — frota de um tenant é uma lista curta o bastante para caber inteira; a mesma decisão
    já vale para Cliente/Motorista abaixo)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListVehicleManagementResultsQuery) -> list[VehicleResultDTO]:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            trip_aggs = await repo.trip_aggregates_by_vehicle(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            maintenance_predicted = await repo.maintenance_predicted_by_vehicle(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            maintenance_realized = await repo.maintenance_realized_by_vehicle(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            other_realized = await repo.other_vehicle_costs_realized(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            vehicle_ids = set(trip_aggs) | set(maintenance_predicted) | set(maintenance_realized) | set(other_realized)
            identities = await repo.fetch_vehicle_identities(
                tenant_id=query.actor.tenant_id, vehicle_ids=list(vehicle_ids)
            )

        results = [
            build_vehicle_result(
                vehicle_id=vehicle_id, plate=identities[vehicle_id][0], model=identities[vehicle_id][1],
                trip_agg=trip_aggs.get(vehicle_id, TripAggregate(0, _ZERO, _ZERO, _ZERO, _ZERO, None)),
                maintenance_predicted=maintenance_predicted.get(vehicle_id, _ZERO),
                maintenance_realized=maintenance_realized.get(vehicle_id, _ZERO),
                other_realized=other_realized.get(vehicle_id, _ZERO),
            )
            for vehicle_id in vehicle_ids
            if vehicle_id in identities
        ]
        results.sort(key=lambda r: r.totals.realized_margin, reverse=True)
        return results
