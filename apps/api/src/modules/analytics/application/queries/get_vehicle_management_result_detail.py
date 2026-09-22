from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.management_result_dto import (
    VehicleCostOriginDTO,
    VehicleResultDetailDTO,
)
from modules.analytics.application.queries.list_trip_management_results import trip_model_to_result_dto
from modules.analytics.application.queries.list_vehicle_management_results import build_vehicle_result
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ZERO = Decimal("0")


@dataclass(frozen=True)
class GetVehicleManagementResultDetailQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    date_from: date | None = None
    date_to: date | None = None


class GetVehicleManagementResultDetailHandler(
    QueryHandler[GetVehicleManagementResultDetailQuery, VehicleResultDetailDTO]
):
    """Drill-down "Veículo → resultado → viagens → custos → OS/CP de origem" (Lote 4) — cada real de
    Manutenção/Outros Custos é rastreável até a Conta a Pagar (e, quando aplicável, a Ordem de
    Serviço) que o originou."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetVehicleManagementResultDetailQuery) -> VehicleResultDetailDTO:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            identities = await repo.fetch_vehicle_identities(
                tenant_id=query.actor.tenant_id, vehicle_ids=[query.vehicle_id]
            )
            if query.vehicle_id not in identities:
                raise NotFoundError("ANALYTICS_VEHICLE_NOT_FOUND", "Veículo inexistente.")
            plate, model = identities[query.vehicle_id]

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
            result = build_vehicle_result(
                vehicle_id=query.vehicle_id, plate=plate, model=model,
                trip_agg=trip_aggs.get(query.vehicle_id, TripAggregate(0, _ZERO, _ZERO, _ZERO, _ZERO, None)),
                maintenance_predicted=maintenance_predicted.get(query.vehicle_id, _ZERO),
                maintenance_realized=maintenance_realized.get(query.vehicle_id, _ZERO),
                other_realized=other_realized.get(query.vehicle_id, _ZERO),
            )

            trips, _total = await repo.list_trips(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to,
                vehicle_id=query.vehicle_id, page=1, limit=200,
            )
            payables = await repo.list_vehicle_cost_payables(
                tenant_id=query.actor.tenant_id, vehicle_id=query.vehicle_id,
                date_from=query.date_from, date_to=query.date_to,
            )

        cost_origins = [
            VehicleCostOriginDTO(
                accounts_payable_id=p.id, origin=p.origem, maintenance_order_id=p.ordem_servico_id,
                value=p.valor, competencia=p.competencia, status=p.status,
            )
            for p in payables
        ]
        return VehicleResultDetailDTO(
            result=result, trips=[trip_model_to_result_dto(t) for t in trips], cost_origins=cost_origins,
        )
