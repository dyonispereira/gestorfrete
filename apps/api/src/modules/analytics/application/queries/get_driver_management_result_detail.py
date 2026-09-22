from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.management_result_dto import (
    DriverLinkedCostDTO,
    DriverResultDetailDTO,
)
from modules.analytics.application.queries.list_driver_management_results import build_driver_result
from modules.analytics.application.queries.list_trip_management_results import trip_model_to_result_dto
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ZERO = Decimal("0")
_ZERO_AGG = TripAggregate(trip_count=0, predicted_revenue=_ZERO, realized_revenue=_ZERO, predicted_cost=_ZERO, realized_cost=_ZERO, km=None)


@dataclass(frozen=True)
class GetDriverManagementResultDetailQuery(Query):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    date_from: date | None = None
    date_to: date | None = None


class GetDriverManagementResultDetailHandler(
    QueryHandler[GetDriverManagementResultDetailQuery, DriverResultDetailDTO]
):
    """Drill-down do Motorista (Lote 4) — mostra as Viagens que compõem `trip_cost_realized` e, à
    parte, os lançamentos explicitamente vinculados (`linked_costs`) que compõem
    `linked_cost_realized` — nunca confundidos entre si."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetDriverManagementResultDetailQuery) -> DriverResultDetailDTO:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            identities = await repo.fetch_driver_identities(
                tenant_id=query.actor.tenant_id, driver_ids=[query.driver_id]
            )
            if query.driver_id not in identities:
                raise NotFoundError("ANALYTICS_DRIVER_NOT_FOUND", "Motorista inexistente.")
            name = identities[query.driver_id]

            trip_aggs = await repo.trip_aggregates_by_driver(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            linked_costs = await repo.driver_linked_costs_realized(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            result = build_driver_result(
                driver_id=query.driver_id, name=name,
                trip_agg=trip_aggs.get(query.driver_id, _ZERO_AGG),
                linked_cost=linked_costs.get(query.driver_id, _ZERO),
            )

            trips, _total = await repo.list_trips(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to,
                driver_id=query.driver_id, page=1, limit=200,
            )
            payables = await repo.list_driver_linked_payables(
                tenant_id=query.actor.tenant_id, driver_id=query.driver_id,
                date_from=query.date_from, date_to=query.date_to,
            )

        linked_cost_items = [
            DriverLinkedCostDTO(
                accounts_payable_id=p.id, origin=p.origem, value=p.valor, competencia=p.competencia, status=p.status,
            )
            for p in payables
        ]
        return DriverResultDetailDTO(
            result=result, trips=[trip_model_to_result_dto(t) for t in trips], linked_costs=linked_cost_items,
        )
